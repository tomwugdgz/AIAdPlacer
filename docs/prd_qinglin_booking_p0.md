# PRD · 青柠/AIAdPlacer — Booking 真实锁位模块（P0 增量）

> 文档类型：产品需求文档（PRD，简单版）
> 模块：Booking 真实锁位（演示态锁点/导点 → 真实物理防超卖）
> 负责人：产品经理 许清楚（pm）
> 委派：主理人 齐活林
> 日期：2026-08-17
> 状态：待架构师裁定关键设计点

---

## 0. 数据与地基核实备注（PM 实测，供架构师校准）

PRD 撰写前我直接核对了代码与库，发现两处与「已核实事实」描述**不一致**，已按设计影响分别标注，不默认推翻原描述，但提请主理人/架构师校准：

1. **SQLite 真实库存库实际内容**（路径 `backend/data/qinlin_local.db`）：
   - 实测为 **7 个内容表**，合计约 **117,992 行**：门禁点位 66,308 / 客户通讯录 26,895 / 智能屏L9 9,801 / 智能屏202507 4,488 / 单元门点位 8,114 / 商场LED点位 1,365 / 道闸点位 1,021。
   - 原描述称「10 表 / 141,820 行（含电梯框架 19,024、梯影 4,327、城市资源索引 477）」。实测**缺这三张表**。
2. **点位「级别」字段缺失**：原描述称库存含 `级别(A++/A+/A/B/C)`。实测各表**无点位级级别列**，仅 `商场LED点位` 有一列 `城市级别`（城市维度，非点位 A++/A+/A/B/C）。

**设计影响**：
- 需求 #3「按 point 的 level 取锁位期限」的 `level` 来源**当前在库存中不存在**，必须在 ETL/归一化阶段**派生**（来源待定：城市级别？楼盘均价？入住率？需架构师裁定）。
- 库存为**多表、异构 schema**，天然不适合直接被 Booking 外键引用 → 强化下文「point_id 映射」对**方案 A（ETL 归一化进 PG）**的倾向。

---

## ① 产品目标

**一句话目标**：把青柠助手「锁点/导点」从演示态（仅返回 `DEMO-*` + 写审计日志、不占用资源）升级为**真实锁位事务**，在 PostgreSQL 层以「档期排他约束」实现物理防超卖，使同一点位同一档期有且仅有 1 个有效占用（SELECTED/LOCKED/PUBLISHED），超卖率 = 0。

**P0 范围边界**
- 交付：Booking 实体 + PG 档期排他 + 五档锁位期限参数 + 四层锁位防护 + qinglin 演示态升级 + 超卖压测验收。
- 不交付（见 P1/P2）：完整方案流 Plan/PlanItem、Point 生命周期状态机、RBAC 数据范围/脱敏、结构化审计、AI 三重校验、经营大盘等。

**成功指标（P0 验收口径）**
- 超卖率 = 0（同 point_id 的 LOCKED/PUBLISHED 档期区间无任何重叠）。
- 百并发锁同一点位仅 1 成功；锁位到期自动释放；幂等键去重；直插重叠 LOCKED 被 DB 约束拦截（23P01）；进程强杀无脏数据。
- qinglin `/chat` 锁点/导点返回**真实 `booking_no`**，不再返回 `DEMO-*`，且 `demo` 标记置否。

---

## ② 用户故事（按角色 × 场景）

| # | 角色 | 场景 | 用户故事 | 验收口径 |
|---|------|------|----------|----------|
| US-1 | sale（销售） | 对话锁点 | 作为销售，我在青柠对话里说"锁一下朝阳区XX楼盘门禁点位 9.1–9.30"，系统应返回真实锁位单号并在档期内独占该点位，让我敢跟客户承诺档期。 | 返回 `booking_no` 且 PG `bookings` 落 LOCKED 行；该点位同档期再锁被拒。 |
| US-2 | sale | 锁位到期前续期 | 作为销售，A++ 点位锁了 10 天快到期，我想延长 5 天，系统应按档位允许续期 1 次并更新 `lockExpireAt`。 | 续期后 `lockExpireAt` 顺延；超出允许次数被拒并提示。 |
| US-3 | media（媒介） | 档期冲突预检 | 作为媒介，排期前先查某点位某档期是否可锁，系统应秒级返回可用性，避免盲锁。 | `/bookings/availability` 返回 `available:bool` 且与最终锁位结果一致。 |
| US-4 | sale | 导点带真实锁位 | 作为销售，导点时导出的清单应带我已真实锁定的点位与档期，而非样例数据。 | 导出内容含真实 `booking_no`/档期；`demo` 标记置否。 |
| US-5 | media | 释放/取消锁位 | 作为媒介，客户放弃后我能释放锁位或登记取消原因，档期立即可被人占用。 | RELEASED/CANCELLED 后该档期 `availability` 恢复可用。 |
| US-6 | engineer（工程） | 安装核验 | 作为工程，锁位点位安装后我标记 INSTALLED→VERIFIED，异常标 ABNORMAL。 | `installStatus` 流转被记录，异常不进入 PUBLISHED。 |
| US-7 | developer（商业开发） | 防超卖审计 | 作为商业开发，我能查任意点位档期占用与排他约束生效情况，确认无超卖。 | 审计可见排他约束拦截记录与锁位流水。 |

---

## ③ 需求池

### P0 必做（验收项）

#### P0-1 · Booking 实体与数据模型
- **内容**：在 PostgreSQL `ai_adplacer` 新增 `bookings` 表。最小售卖单元=档期。
- **字段**：`booking_no`(业务单号,唯一)、`point_id`、`plan_id`(可空)、`customer_id`、`start_date`、`end_date`、`status`(枚举 SELECTED/LOCKED/PUBLISHED/RELEASED/EXPIRED/CANCELLED/TERMINATED)、`lock_expire_at`、`idempotency_key`(幂等)、价格快照 `unit_price_snapshot`/`weeks`/`discount_rate`/`extra_fee`/`final_amount`、安装 `install_status`(PENDING/INSTALLED/VERIFIED/ABNORMAL)、`cancel_reason`、`created_at`、`updated_at`。
- **验收**：DDL 可在 `ai_adplacer` 执行；`booking_no`、`idempotency_key` 唯一；状态/安装枚举受约束（CHECK 或枚举类型）。

#### P0-2 · PG 档期排他约束（防超卖核心）
- **内容**：启用 `btree_gist`；在 `bookings` 上加
  `EXCLUDE USING gist (point_id WITH =, daterange(start_date,end_date,'[]') WITH &&) WHERE (status IN ('LOCKED','PUBLISHED'))`。
- **验收**：同 `point_id` 的 LOCKED/PUBLISHED 区间重叠插入/更新被拒，报 `23P01`；SELECTED/RELEASED 等不触发排他。

#### P0-3 · 五档锁位期限参数表（可配置）
- **内容**：新增 `lock_tier_config`（`level`,`base_days`,`extend_times`,`extend_days`）。默认值：A++ 10/1/5、A+ 7/1/3、A 7/1/3、B 3/1/2、C 3/0/0。
- **验收**：锁位时按 `point.level` 取档计算 `lock_expire_at`；续期次数/天数受该表约束；参数可后台改而不改代码。

#### P0-4 · 四层锁位防护
- **内容**：① 接口预检 `/bookings/availability`；② Redis 分布式锁 `lock:point:{id}`（`SET NX PX`）；③ DB 悲观锁 `SELECT … FOR UPDATE ORDER BY id`；④ DB 排他约束（P0-2）。
- **验收**：四层任一层拦截都返回一致"不可锁"结论；压测 CT-01 仅 1 成功。

#### P0-5 · 升级 qinglin 演示态
- **内容**：`/api/v2/assistant/chat` 的 `ACTION_POINT_LOCK`、`ACTION_POINT_EXPORT` 改为调用真实 Booking 锁位/导出事务；`submit_report`(报备) **本轮保留演示态**（建议，见待确认 #2）。返回真实 `booking_no`，`demo` 标记置否；失败回滚并保留审计。
- **验收**：锁点返回真实 `booking_no` 非 `DEMO-*`；`demo:false`；异常时资源不残留（对照 CT-05）。

#### P0-6 · 锁位到期与释放（cron + 状态机最小集）
- **内容**：定时任务扫描 `LOCKED` 且 `lock_expire_at` 过期 → 置 `EXPIRED` 并释放档期；提供释放/取消接口写 `cancel_reason`。
- **验收**：到期自动 EXPIRED，档期恢复可用（CT-02）；取消后同档期可重新锁。

#### P0-7 · 超卖压测验收标准（取自 MediaPlaner 说明书 §6.7，作为 P0 门禁）
- **CT-01** 同一点位百并发锁位仅 1 成功。
- **CT-02** 锁位到期 cron 自动释放，档期可再锁。
- **CT-03** 幂等键去重：同 `idempotency_key` 重复请求返回同一 `booking_no`，不重复建单。
- **CT-04** 绕过应用层直插重叠 LOCKED → 触发 `23P01`（约束兜底生效）。
- **CT-05** 进程强杀（锁位事务中途 kill）→ 无脏数据（原子事务 + 约束）。
- **CT-06** 四层防护下并发混合操作（锁/续/释/查）最终一致性：超卖率 = 0。

### P1（后续，建议列入下一迭代）
- **P1-1** Plan / PlanItem 完整方案流（多 Booking 聚合为一个投放方案）。
- **P1-2** Point Lifecycle 状态机（点位级上下架/维护）。
- **P1-3** RBAC 数据范围（按城市/角色可见性）与字段脱敏（手机号等）。
- **P1-4** `StatusTransitionLog` + 结构化 `AuditLog`（替代当前明文 JSON 审计）。
- **P1-5** AI 服务端三重校验（意图→库存→档期一致性）。
- **P1-6** 报备（report）真实化（接入 CRM 工单流转）—— 见待确认 #2。

### P2（远期）
- **P2-1** 经营大盘指标（锁位转化率、占用率、超卖未遂计数）。
- **P2-2** 投放/锁位 PDF 规范导出。
- **P2-3** 供应商管理与巡检工单。

---

## ④ UI / 接口设计稿建议

### 4.1 端点清单（建议）
| 方法 | 路径 | 说明 | 关键入参 | 关键出参 |
|------|------|------|----------|----------|
| POST | `/api/v2/bookings/precheck` (或 `/bookings/availability`) | 档期预检（防护①） | `point_id`,`start_date`,`end_date` | `available`,`conflict_booking_no?` |
| POST | `/api/v2/bookings` | 创建真实锁位（走四层防护，返回 `booking_no`） | `point_id`,`customer_id`,`start_date`,`end_date`,`plan_id?`,`idempotency_key`,价格快照 | `booking_no`,`status`,`lock_expire_at` |
| POST | `/api/v2/bookings/{booking_no}/extend` | 续期（受 P0-3 档位约束） | `extend_days` | `lock_expire_at` |
| POST | `/api/v2/bookings/{booking_no}/release` | 释放（→RELEASED） | `reason?` | `status` |
| POST | `/api/v2/bookings/{booking_no}/cancel` | 取消（→CANCELLED，写 `cancel_reason`） | `cancel_reason` | `status` |
| GET | `/api/v2/bookings?point_id=&status=` | 锁位查询 | 过滤条件 | 列表 |
| POST | `/api/v2/bookings/{booking_no}/install` | 安装状态流转 | `install_status` | `install_status` |
| GET | `/api/v2/bookings/point/{point_id}/timeline` | 某点位档期占用时间轴（UI 用） | `point_id` | 占用区间列表 |
| （内部） | `POST /api/v2/assistant/chat` | 已存在；锁点/导点动作改调真实 Booking | — | 返回真实 `booking_no`,`demo:false` |

### 4.2 关键字段约定
- `booking_no`：业务可读单号（如 `BK-YYYYMMDD-XXXXXX`），与 PG 主键 `id`(UUID) 分离。
- `point_id`：见待确认 #1（倾向引用 PG `media_resources.id`）。
- `idempotency_key`：客户端/对话 session 生成，防重复提交（CT-03）。
- `lock_expire_at`：由 P0-3 档位 + 续期推导，UTC 存储。
- 价格快照：锁位瞬间固化，避免后续刊例价变动影响已锁单。

### 4.3 前端（青柠助手侧）建议
- 锁点结果卡：展示真实 `booking_no`、点位、档期、`lock_expire_at` 倒计时、续期入口。
- 档期时间轴组件：调用 `/timeline` 可视化占用，预检冲突高亮。
- 导点结果：从真实 `bookings` 拉已锁清单，替换样例数据。

---

## ⑤ 待确认问题（主理人转交架构师）

1. **【关键】`point_id` 指向谁？（PM 倾向：方案 A）**
   - **方案 A**：将 SQLite 真实库存（异构多表）**ETL 归一化进 PG `media_resources`**，补齐 `level/city/area/project/point_no/media_type` 字段；Booking 引用 `media_resources.id`（PG 为 SSOT，符合说明书 A1 原则）。
     - *倾向理由*：① 库存为只读、异构、无点位级 level，归一化后才能稳定支撑 P0-3「按 level 取档」；② 排他约束 `EXCLUDE` 与悲观锁 `FOR UPDATE` 需同库事务才干净，跨库无法在 DB 层防超卖；③ 外键完整性、未来 Plan/PlanItem 关联更简单。
     - *前提*：需裁定 ETL 频率与主从关系（SQLite 为上游镜像？还是 PG 反哺为主库？），以及 **level 如何派生**（实测库存无 A++/A+/A/B/C 列，见 §0）。
   - **方案 B**：Booking 直接存 SQLite 点位自然键，PG 只管锁位与排他，展示跨库 join。
     - *取舍*：改动小但跨库无法在 DB 层做排他约束，且 level 仍需另行维护。
   - **裁定项**：最终由架构师裁定；PM 建议 A，并要求先解决 level 派生来源。

2. **报备（report）本轮是否真实化？**
   - PM 建议：**P0 保留演示态**（仅写审计 + CRM 工单占位），不接真实资源占用；真实化列入 P1-6。理由：报备属客户意向/CRM 流转，非资源占用，与 P0「物理防超卖」核心目标无直接关系，且当前无 CRM 系统对接。请主理人确认是否采纳。

3. **库存数据 discrepancy 校准**：请主理人/架构师确认 §0 所述缺失表（电梯框架/梯影/城市资源索引）与级别字段缺失是「本地副本不全」还是「数据源已变」，以决定 ETL 上游与 level 派生规则。

4. **Redis 锁粒度与超时**：`lock:point:{id}` 的 PX 超时建议与 DB 事务时长匹配（建议 3–5s），避免长事务下锁提前释放造成防护空窗，请架构师核定。

5. **档期边界语义**：`daterange(start,end,'[]')` 含端点，需确认 `end_date` 为"最后展示日"还是"次日起释放"，以统一预检与约束口径。
