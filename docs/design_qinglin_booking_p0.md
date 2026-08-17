# 设计文档 · 青柠/AIAdPlacer — Booking 真实锁位模块（P0 增量）

> 文档类型：架构设计（标准 SOP 第二阶段产出）
> 角色：架构师 高见远（Gao）
> 模块：Booking 真实锁位（演示态锁点/导点 → 真实物理防超卖）
> 日期：2026-08-17
> 状态：交付工程师寇豆码实现、QA 严过关验收
> 品牌铁律：全项目不得出现「亲邻」字眼，统一用「青柠」/ 代码 `qinglin`

---

## 0. 范围与决策基线

### 0.1 已拍板的两个设计岔路（Tom 裁定，本设计照此执行）
1. **锁位级别来源 = 类型 + 城市映射（可配置）**：真实 SQLite 库存各表**无任何 level 列**（已亲验 `LEVEL_COLUMNS_FOUND: []`），五档锁位参数（A++/A+/A/B/C）的级别必须在 **ETL/归一化阶段派生**并写入 PG `media_resources.level`。派生规则由一张**可配置映射表**驱动（媒体类型 × 城市分级 → 默认 level），并支持核心城区 +1 档（封顶 A++）。
2. **点位映射 = 方案 A（ETL 进 PG）**：写 ETL/归一化脚本，读 SQLite 6 张媒体表 → 补全 `level/city/area/project/point_no/media_type` → 写入 PG `media_resources`，使 PG 成为 **SSOT**；Booking 引用 `media_resources.id`。SQLite **只读参考，禁止应用层改写，绝不跨库 join**。

### 0.2 已核实真实技术地基（主理人亲验，不再质疑）
| 项 | 值 |
|---|---|
| PG 库 | `postgresql://quantdinger:quantdinger123@127.0.0.1:5432/ai_adplacer`（库名 `ai_adplacer`，非 `quantdinger`，`config.py:14`） |
| Redis | `redis://127.0.0.1:6379/0`（`config.py:17`），依赖 `redis>=5.0.0`（自带 `redis.asyncio`） |
| 真实 SQLite 主库 | `backend/app/data/qinlin_local.db`，**只读**；6 张媒体表（门禁 66308 / 单元门 8114 / 智能屏L9 9801 / 智能屏202507 4488 / 商场LED 1365 / 道闸 1021）+ 客户通讯录 26895（通讯录非媒体）；各表**无 level 列** |
| PG 已有模型 | `MediaResource`(`media_resources`/`Campaign`/`CampaignMedia`/`Placement`/`Conversion`)，落在 `ai_adplacer`；`media_resources` 与 SQLite 异构（缺 `level/city/area/project/point_no`） |
| PG 扩展 | `btree_gist` **已可用**（排他约束前提） |
| 演示态现状 | `qinglin_assistant/workflows/sale_media.py` 报备/锁点/导点 `demo:True`，返回 `DEMO-*` + 写审计日志，不占用资源 |

### 0.3 与现有代码库的关键偏差（工程落地须知）
- 现有 `app/models/__init__.py` 使用**同步 SQLAlchemy**（`create_engine` + `SessionLocal` + `Base.metadata.create_all`），且没有 Alembic、没有 `routers/core/tasks` 目录。
- 本设计采用 Tom 指定的异步栈（`SQLAlchemy async + asyncpg + Alembic`），落地方式为：**在同一个 `Base`（同步 declarative）上新增 Booking 相关模型**，并**并行新增一个 async 引擎 + `AsyncSession`** 供 Booking 模块使用，现有同步引擎/会话完整保留（SQLAlchemy 2.0 允许 async session 操作同步映射类）。Alembic 用 async env 生成 DDL。这样既不改动存量代码，又能满足异步栈要求。
- 若工程评估认为全量 async 化风险更低，可改为整体迁移——见 §8 待明确。

---

## 1. 实现方案 + 框架选型

**语言/框架**：Python 3.11 + FastAPI（已在用）+ SQLAlchemy 2.0（async 引擎并行）。

**存储分治（重申）**：
- **PostgreSQL `ai_adplacer` = SSOT**：承载 `media_resources`（经 ETL 补全）、`bookings`、`lock_tier_config`、`media_level_rule`。锁位/档期/排他约束全部落在 PG。
- **SQLite `qinlin_local.db` = 只读参考**：仅 ETL 读取，应用层任何写操作禁止；不跨库 join。
- **Redis = 分布式锁 + 轻量去重**：仅做并发串行化（层②），不做资源占用真相来源。

**选型清单**：
- Web：FastAPI（`main.py` 已有挂载 `/api/v2/assistant`；新增 booking 路由挂 `/api/v2/bookings`）。
- ORM：SQLAlchemy 2.0 async（`AsyncSession` + `asyncpg` 驱动）。
- 迁移：**Alembic**（async env），承担 `media_resources` 加列 + 新建表 + `btree_gist` + 排他约束 + 种子数据。
- 排他约束：`btree_gist` + `EXCLUDE USING gist`（见 §P0-2）。
- 分布式锁：`redis.asyncio`（`SET NX PX`）。
- 定时释放：**APScheduler**（`BackgroundScheduler`，注册于 FastAPI `startup`），扫描 `LOCKED` 过期自动释放（见 §P0-6）。APScheduler 为新增轻依赖，与现有栈无冲突；Windows/Linux 均可运行。备选：独立脚本 `booking_release.py` 由 OS 计划任务调用（同样提供）。

---

## 2. 文件清单及相对路径（新建 / 修改）

> 所有路径相对 `backend/`。磁盘 SQLite 文件名保持 `qinlin_local.db`、SQLite 表名**不动**；代码侧标识符一律 `qinglin`。

| 类型 | 路径 | 说明 |
|---|---|---|
| 新建 | `app/models/booking.py` | `Booking`、`LockTierConfig`、`MediaLevelRule` 模型 + 枚举（`BookingStatus`/`InstallStatus`/`LockTier`），挂在已有 `Base` 上 |
| 新建 | `app/schemas/booking.py` | Pydantic v2 schemas：`BookingCreate`/`BookingExtend`/`BookingRelease`/`BookingCancel`/`BookingRead`/`AvailabilityQuery`/`AvailabilityResult` |
| 新建 | `app/services/booking_service.py` | 锁位四层防护编排、续期、释放、取消、预检、幂等、档期 timeline |
| 新建 | `app/services/etl_media.py` | 读 SQLite 6 表 → 派生 level → upsert PG `media_resources`（幂等、可重跑） |
| 新建 | `app/services/level_rule.py` | `derive_level(media_type, city)` 派生逻辑 + 读取 `media_level_rule` 配置 |
| 新建 | `app/core/distributed_lock.py` | `redis.asyncio` 分布式锁封装：`acquire/release`（SET NX PX、token 防误删、上下文管理器） |
| 新建 | `app/core/exceptions.py` | 青柠业务异常 + 错误码映射（见 §7） |
| 新建 | `app/routers/bookings.py` | REST 路由：`/precheck` `/ ` `/{booking_no}/extend` `/release` `/cancel` `/install` `/timeline` 等（PRD §4.1） |
| 新建 | `app/tasks/booking_release.py` | 到期释放 job（`release_expired_bookings()`）+ 可作为 APScheduler 入口 / 独立脚本 |
| 新建 | `app/tasks/scheduler.py` | APScheduler `BackgroundScheduler` 装配与启动（FastAPI `startup` 调用） |
| 新建 | `alembic.ini` + `migrations/env.py` + `migrations/versions/0001_booking.py` | Alembic 配置（async env）+ 首版迁移（DDL 见 §P0-2）+ 种子数据 |
| 新建 | `tests/test_booking_ct.py` | CT-01~CT-06 压测用例（pytest + 并发 / 直插 SQL） |
| 新建 | `tests/test_etl_media.py` | ETL 幂等 / 派生 level 单测 |
| **修改** | `app/qinglin_assistant/workflows/sale_media.py` | `lock_point()`/`export_point()` 改为调用真实 `booking_service`（P0-5）；`submit_report()` **保留演示态** |
| **修改** | `app/qinglin_assistant/api/routes.py` | `ACTION_POINT_LOCK`/`ACTION_POINT_EXPORT` 分支把 `params`（point_type/city/...）解析为 `media_resource_id` 后转交 `booking_service`（接入点：`routes.py:275-281`） |
| **修改** | `app/main.py` | 注册 `bookings_router`（`prefix="/api/v2/bookings"`）；在 `startup` 中启动 APScheduler（调用 `app.tasks.scheduler.start`）；保留现有 `init_db()` |
| **修改** | `app/config.py` | 新增 `BOOKING_LOCK_PX_MS: int = 5000`（Redis 锁超时，对应待确认#4）、`BOOKING_RELEASE_CRON_SECONDS: int = 60`；无需改 DATABASE_URL/REDIS_URL |
| **修改** | `backend/requirements.txt` | 取消注释/新增 `asyncpg`、`alembic`（见 §6） |
| **修改** | `app/models/__init__.py` | `from app.models.booking import *` 纳入 `Base` 元数据（确保 `create_all`/Alembic autogenerate 可见） |

---

## 3. 数据结构与接口

### 3.1 ER 文字描述
- **media_resources（PG，已存在，ETL 补全）**：主键 `id`(UUID)。ETL 新增列：`level`(LockTier，派生)、`city`、`area`、`project`、`point_no`、`source_table`(来源 SQLite 表名)、`dedup_key`(去重键)、`media_type_code`(媒体类型编码)。`bookings.media_resource_id → media_resources.id`（FK）。
- **bookings（PG，新建）**：核心锁位实体。见 §P0-1 字段清单。`media_resource_id` FK→`media_resources.id`；`campaign_id` 可空 FK→`campaigns.id`；`lock_tier` 落库时快照（独立于 `media_resources.level` 后续变化）。
- **lock_tier_config（PG，新建）**：五档锁位参数（P0-3）。PK `level`(LockTier)，`base_days`/`extend_times`/`extend_days`。
- **media_level_rule（PG，新建）**：level 派生配置（P0 决策①）。`match_type`(media_type|city)、`match_key`(媒体类型编码或城市/城区名)、`level`、`priority`、`enabled`。
- **campaigns / campaigns_media / placements / conversions**：已有，Booking 不强制依赖（`campaign_id` 可空，P1 再强关联 Plan/PlanItem）。

### 3.2 主要 Pydantic Schema（节选）
```python
# app/schemas/booking.py
class AvailabilityQuery(BaseModel):
    media_resource_id: UUID
    lock_start: date           # PRD start_date
    lock_end: date             # PRD end_date（含端点，最后展示日）

class AvailabilityResult(BaseModel):
    available: bool
    conflict_booking_no: str | None = None

class BookingCreate(BaseModel):
    media_resource_id: UUID
    customer_id: str | None = None
    campaign_id: UUID | None = None
    lock_start: date
    lock_end: date
    idempotency_key: str | None = None   # 不传则由服务端按会话+点位+档期生成
    created_by: str | None = None
    # 价格快照（可选，锁位瞬间固化；不传则留空）
    unit_price_snapshot: Decimal | None = None
    weeks: int | None = None
    discount_rate: Decimal | None = None
    extra_fee: Decimal | None = None
    final_amount: Decimal | None = None

class BookingExtend(BaseModel):
    extend_days: int | None = None   # 不传则取该档位 extend_days

class BookingCancel(BaseModel):
    cancel_reason: str

class BookingRead(BaseModel):
    id: UUID
    booking_no: str
    media_resource_id: UUID
    lock_tier: str
    lock_start: date
    lock_end: date
    expire_at: datetime
    status: str
    install_status: str
    idempotency_key: str
    created_at: datetime
    updated_at: datetime
```

---

## 4. P0-1 · Booking 实体与状态机

### 4.1 字段清单（`bookings` 表）
| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `id` | UUID | PK, default `gen_random_uuid()` | 代理主键 |
| `booking_no` | VARCHAR(32) | UNIQUE NOT NULL | 业务单号 `BK-YYYYMMDD-XXXXXX` |
| `media_resource_id` | UUID | FK→`media_resources.id`, NOT NULL | 占用的点位（PRD 的 `point_id` 即此） |
| `campaign_id` | UUID | FK→`campaigns.id`, 可空 | 关联投放方案（P1 强关联） |
| `customer_id` | VARCHAR(64) | 可空 | 客户标识（通讯录维度，P1 规整） |
| `lock_tier` | LockTier | NOT NULL | 落库时快照的档位（A++/A+/A/B/C） |
| `lock_start` | DATE | NOT NULL | 档期起始（含端点，本地营业日） |
| `lock_end` | DATE | NOT NULL | 档期结束（含端点，最后展示日） |
| `expire_at` | TIMESTAMPTZ | NOT NULL | LOCKED 未转 PUBLISHED 的过期时刻（UTC） |
| `status` | BookingStatus | NOT NULL DEFAULT 'SELECTED' | 状态机 |
| `idempotency_key` | VARCHAR(128) | UNIQUE NOT NULL | 幂等键（CT-03） |
| `unit_price_snapshot` / `weeks` / `discount_rate` / `extra_fee` / `final_amount` | 数值 | 可空 | 价格快照（锁位瞬间固化） |
| `install_status` | InstallStatus | DEFAULT 'PENDING' | 安装流转（US-6） |
| `cancel_reason` | TEXT | 可空 | 取消原因 |
| `created_by` | VARCHAR(64) | 可空 | 操作人（RBAC 角色） |
| `created_at` / `updated_at` | TIMESTAMPTZ | DEFAULT now() | 时间戳 |

CHECK：`lock_end >= lock_start`。

### 4.2 状态机（mermaid stateDiagram）
```mermaid
stateDiagram-v2
    [*] --> SELECTED
    SELECTED --> LOCKED : 确认锁位(设 expire_at)
    SELECTED --> CANCELLED : 取消(写原因)
    LOCKED --> PUBLISHED : 上刊确认(install VERIFIED)
    LOCKED --> RELEASED : 主动释放
    LOCKED --> CANCELLED : 取消(写原因)
    LOCKED --> EXPIRED : cron 到点未转 PUBLISHED
    PUBLISHED --> TERMINATED : 提前下刊
    EXPIRED --> [*]
    RELEASED --> [*]
    CANCELLED --> [*]
    TERMINATED --> [*]
```

### 4.3 合法转移矩阵表
| 源状态 | 目标状态 | 触发 | 占用档期? | 释放 Redis 锁 |
|---|---|---|---|---|
| — | SELECTED | 创建（预选，未占用） | 否 | — |
| SELECTED | LOCKED | 确认锁位 | **是**（进入排他） | 事务提交后释放层②锁 |
| SELECTED | CANCELLED | 取消 | 否 | — |
| LOCKED | PUBLISHED | 上刊确认 | 是（持续占用） | — |
| LOCKED | RELEASED | 主动释放 | 否（释放档期） | 是 |
| LOCKED | CANCELLED | 取消 | 否（释放档期） | 是 |
| LOCKED | EXPIRED | cron 自动 | 否（释放档期） | 是 |
| PUBLISHED | TERMINATED | 提前下刊 | 否（释放档期） | — |
| EXPIRED / RELEASED / CANCELLED / TERMINATED | — | 终态，无出边 | 否 | — |

> 排他约束仅对 `LOCKED`/`PUBLISHED` 生效（`SELECTED` 不占用，符合 PRD 备注）。

---

## 5. P0-2 · PG 档期排他约束（防超卖核心 DDL）

完整迁移 DDL（由 Alembic `0001_booking.py` 执行，**最后防线**）。绕过应用层直插重叠 LOCKED 会触发 `23P01`。

```sql
-- ① 扩展（前提，已验证可用）
CREATE EXTENSION IF NOT EXISTS btree_gist;

-- ② media_resources 补全派生字段（ETL 写入）
ALTER TABLE media_resources
  ADD COLUMN IF NOT EXISTS level        VARCHAR(4),       -- A++/A+/A/B/C（派生）
  ADD COLUMN IF NOT EXISTS city         VARCHAR(64),
  ADD COLUMN IF NOT EXISTS area         VARCHAR(64),
  ADD COLUMN IF NOT EXISTS project      VARCHAR(128),
  ADD COLUMN IF NOT EXISTS point_no     VARCHAR(64),
  ADD COLUMN IF NOT EXISTS source_table VARCHAR(64),      -- 来源 SQLite 表名
  ADD COLUMN IF NOT EXISTS dedup_key    VARCHAR(128),     -- 去重键
  ADD COLUMN IF NOT EXISTS media_type_code VARCHAR(32);   -- 媒体类型编码
CREATE INDEX IF NOT EXISTS ix_media_resources_dedup ON media_resources(dedup_key);
CREATE INDEX IF NOT EXISTS ix_media_resources_level ON media_resources(level);

-- ③ 枚举
DO $$ BEGIN
  CREATE TYPE booking_status  AS ENUM ('SELECTED','LOCKED','PUBLISHED','RELEASED','EXPIRED','CANCELLED','TERMINATED');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
  CREATE TYPE install_status  AS ENUM ('PENDING','INSTALLED','VERIFIED','ABNORMAL');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
  CREATE TYPE lock_tier       AS ENUM ('A++','A+','A','B','C');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- ④ bookings 主表
CREATE TABLE IF NOT EXISTS bookings (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  booking_no          VARCHAR(32) NOT NULL UNIQUE,
  media_resource_id   UUID NOT NULL REFERENCES media_resources(id),
  campaign_id         UUID REFERENCES campaigns(id),
  customer_id         VARCHAR(64),
  lock_tier           lock_tier NOT NULL,
  lock_start          DATE NOT NULL,
  lock_end            DATE NOT NULL,
  expire_at           TIMESTAMPTZ NOT NULL,
  status              booking_status NOT NULL DEFAULT 'SELECTED',
  idempotency_key     VARCHAR(128) NOT NULL UNIQUE,
  unit_price_snapshot NUMERIC(10,2),
  weeks               INTEGER,
  discount_rate       NUMERIC(5,4),
  extra_fee           NUMERIC(10,2),
  final_amount        NUMERIC(12,2),
  install_status      install_status NOT NULL DEFAULT 'PENDING',
  cancel_reason       TEXT,
  created_by          VARCHAR(64),
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT ck_booking_date_order CHECK (lock_end >= lock_start)
);

-- ⑤ 档期排他约束（核心）：同点位 LOCKED/PUBLISHED 区间重叠即拒
ALTER TABLE bookings DROP CONSTRAINT IF EXISTS booking_no_overlap;
ALTER TABLE bookings ADD CONSTRAINT booking_no_overlap
  EXCLUDE USING gist (
    media_resource_id WITH =,
    daterange(lock_start, lock_end, '[]') WITH &&
  ) WHERE (status IN ('LOCKED','PUBLISHED'));

-- ⑥ 索引（查询/扫描加速）
CREATE INDEX IF NOT EXISTS ix_bookings_media_status ON bookings(media_resource_id, status);
CREATE INDEX IF NOT EXISTS ix_bookings_expire ON bookings(expire_at) WHERE status = 'LOCKED';
CREATE INDEX IF NOT EXISTS ix_bookings_idem ON bookings(idempotency_key);

-- ⑦ 五档参数表 + 种子
CREATE TABLE IF NOT EXISTS lock_tier_config (
  level        lock_tier PRIMARY KEY,
  base_days    INTEGER NOT NULL,
  extend_times INTEGER NOT NULL,
  extend_days  INTEGER NOT NULL
);
INSERT INTO lock_tier_config(level, base_days, extend_times, extend_days) VALUES
  ('A++', 10, 1, 5), ('A+', 7, 1, 3), ('A', 7, 1, 3), ('B', 3, 1, 2), ('C', 3, 0, 0)
ON CONFLICT (level) DO NOTHING;

-- ⑧ level 派生配置表 + 种子（P0 决策①默认规则）
CREATE TABLE IF NOT EXISTS media_level_rule (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  match_type VARCHAR(12) NOT NULL,   -- 'media_type' | 'city'
  match_key  VARCHAR(64) NOT NULL,
  level      lock_tier  NOT NULL,
  priority   INTEGER NOT NULL DEFAULT 0,
  enabled    BOOLEAN NOT NULL DEFAULT true
);
-- 默认：媒体类型 → 基础档（priority 低）
INSERT INTO media_level_rule(match_type, match_key, level, priority) VALUES
  ('media_type','door_access',   'A+', 0),   -- 门禁点位（广告门）
  ('media_type','mall_led',       'A++',0),   -- 商场LED
  ('media_type','smart_screen_l9','A',  0),   -- 智能屏L9
  ('media_type','smart_screen_202507','A',0), -- 智能屏202507
  ('media_type','unit_door',     'B',  0),    -- 单元门点位
  ('media_type','boom_gate',     'C',  0)     -- 道闸
ON CONFLICT DO NOTHING;
-- 默认：核心城区 +1 档（priority 高，覆盖基础档）
INSERT INTO media_level_rule(match_type, match_key, level, priority) VALUES
  ('city','广州天河','A++', 10), ('city','广州珠江新城','A++',10),
  ('city','北京朝阳','A++',10),  ('city','上海浦东','A++',10)
ON CONFLICT DO NOTHING;
```

**绕过应用层直插重叠 LOCKED → 触发 `23P01`**：测试直接 `INSERT` 一条与已有 LOCKED 同 `media_resource_id` 且 `daterange` 重叠、`status='LOCKED'` 的行，PG 返回 `exclude` 冲突（SQLSTATE `23P01`），插入被拒。这是 DB 层最后防线，与四层防护互补。

---

## 6. P0-3 · 五档锁位参数与取档逻辑

### 6.1 参数表（来自 `lock_tier_config`）
| tier | 基础天数 base_days | 可延期次数 extend_times | 每次延长天数 extend_days |
|---|---|---|---|
| A++ | 10 | 1 | 5 |
| A+ | 7 | 1 | 3 |
| A | 7 | 1 | 3 |
| B | 3 | 1 | 2 |
| C | 3 | 0 | 0 |

### 6.2 取档逻辑（结合 P0-1 派生 level）
1. ETL 写入 `media_resources.level`（见 §7 派生规则 + `media_level_rule`）。
2. 锁位时：`lock_tier = media_resource.level`（**落库快照**，后续 level 变更不影响已锁单）。
3. 计算 `expire_at`：`lock_start` 当日 00:00 UTC + `base_days` 天（LOCKED 状态寿命）；续期：`expire_at += extend_days`，累计续期次数 ≤ `extend_times`（C 档为 0 次，续期被拒 `LOCK_QUOTA_EXCEEDED`）。
4. `lock_start`/`lock_end` 为用户声明的**档期展示区间**（含端点），与 `expire_at`（锁位占用寿命）是两个独立维度：档期可长可短，占用寿命到 `expire_at` 未转 PUBLISHED 即释放。

---

## 7. ETL 归一化设计（方案 A 落地）

**脚本**：`app/services/etl_media.py`（CLI：`python -m app.services.etl_media`）。

**字段映射**（SQLite 6 表 → `media_resources`）：
- `id`：由 `dedup_key` 经 `uuid5(NAMESPACE, dedup_key)` **确定性生成**，保证可重跑幂等（`ON CONFLICT (id) DO UPDATE`）。
- `dedup_key = normalize(city + project + building + elevatorNo + mediaType)`（沿用意见书去重键口径，跨源去重）。
- `media_type_code`：按来源表映射 → `door_access / mall_led / smart_screen_l9 / smart_screen_202507 / unit_door / boom_gate`。
- `level`：调用 `derive_level(media_type_code, city)`（见下）。
- `city/area/project/point_no`：从各表原始列取（不同表列名异构，逐表写映射函数；缺失则 NULL）。
- `source_table`：来源表名（溯源）。
- 其余 `media_resources` 既有列（`name/type/category/lat/lng/...`）：尽力映射，缺失保持默认。

**level 派生规则（`app/services/level_rule.py`）**：
```python
def derive_level(media_type_code: str, city: str | None) -> str:
    # 1) 基础档：media_level_rule WHERE match_type='media_type' AND match_key=media_type_code
    base = rule_by_media_type(media_type_code)        # 默认 A+/A++/A/B/C
    # 2) 城市覆盖：match_type='city' 且 city 含 match_key（如 '广州天河'）→ 高 priority 覆盖
    city_rule = rule_by_city(city)                    # 核心城区 +1 档，封顶 A++
    return city_rule.level if (city_rule and city_rule.priority > base.priority) else base.level
```
- 默认派生规则（初值，可在 `media_level_rule` 调）：门禁→A+、商场LED→A++、智能屏L9→A、智能屏202507→A、单元门→B、道闸→C；核心城区（广州天河/珠江新城/北京朝阳/上海浦东…）覆盖为 A++（封顶）。
- 配置可调：改 `media_level_rule` 行即生效，无需改代码。

**运行模式**：
- 全量：每次跑全表 `SELECT`（SQLite 只读），upsert 全量（幂等）。
- 增量：SQLite 无可靠 `updated_at`，P0 默认**全量幂等 upsert**（10 万行量级，分钟级）；如需增量后续加 `source_row_hash` 比对。
- **SQLite 只读**：连接串加 `mode=ro`（`sqlite:///...?mode=ro`）；绝不在 ETL 中写 SQLite。
- PG 写入：经 async session（或同步均可），单事务批量 upsert。

---

## 8. P0-4 · 四层锁位超卖防护（时序图）

四层依次：① 接口预检 `GET/POST /bookings/availability` ② Redis 分布式锁 `SET NX PX`（key 含 `media_resource_id`+档期）③ DB 悲观锁 `SELECT … FOR UPDATE ORDER BY id` ④ DB 排他约束（P0-2）。

```mermaid
sequenceDiagram
    autonumber
    participant C as 调用方(青柠助手/API)
    participant API as bookings 路由
    participant SVC as booking_service
    participant R as Redis(层②)
    participant PG as PostgreSQL(层③④)

    C->>API: POST /bookings (media_resource_id, lock_start, lock_end, idempotency_key)
    API->>SVC: create_booking(...)

    Note over SVC: 层① 接口预检
    SVC->>PG: SELECT 冲突 booking (status IN LOCKED/PUBLISHED 且 daterange 重叠)
    alt 命中冲突
        SVC-->>C: 409 POINT_ALREADY_LOCKED (conflict_booking_no)
    else 无冲突
        Note over SVC,R: 层② Redis 分布式锁
        SVC->>R: SET qinglin:lock:booking:{mr_id}:{start}:{end} NX PX 5000 (token)
        alt 未取到锁(并发他人持有)
            SVC-->>C: 409 POINT_ALREADY_LOCKED (并发串行化)
        else 取到锁
            Note over SVC,PG: 层③ DB 悲观锁
            SVC->>PG: BEGIN; SELECT ... FROM media_resources WHERE id=? FOR UPDATE ORDER BY id
            SVC->>PG: INSERT bookings (status=LOCKED) —— 层④ 排他约束即时校验
            alt 排他冲突(23P01 / IntegrityError)
                PG-->>SVC: rollback
                SVC->>R: DEL 锁(token 校验)
                SVC-->>C: 409 PROTECTION_RULE_VIOLATED
            else 成功
                PG-->>SVC: commit
                SVC->>R: DEL 锁(token 校验)
                SVC-->>C: 200 BookingRead(booking_no, status=LOCKED)
            end
        end
    end
```

**每层失败回滚/释放语义**：
- 层①：纯查询，无副作用，直接返回不可用结论。
- 层②：未取到锁即返回「不可锁」，不进入 DB；锁由 `PX 5000` 自动过期兜底（防进程崩溃残留）。
- 层③：悲观锁在事务内，事务回滚自动释放行锁。
- 层④：排他约束在 `INSERT` 提交时校验；冲突则整事务 rollback，资源零残留。成功后 `DEL` 释放 Redis 锁（带 token 防误删他人锁）。
- **一致性保证**：四层任一拦截都返回一致「不可锁」结论；层④为 DB 物理兜底，确保超卖率=0。

---

## 9. P0-5 · 升级 qinglin 演示态

**改造点**：
- 文件 `app/qinglin_assistant/workflows/sale_media.py`：
  - `lock_point()`：**改为真实占用**。解析 `params` 得到 `media_resource_id`（见接入说明）→ 调 `booking_service.create_booking(...)`，返回真实 `booking_no`，`demo:False`。
  - `export_point()`：**改为真实导出**。从 `bookings` 拉取该客户/会话已锁清单（真实 `booking_no`/档期），`demo:False`。
  - `submit_report()`：**保留演示态**（`demo:True`，仅写审计 + CRM 占位），不接真实资源。
- 文件 `app/qinglin_assistant/api/routes.py`（接入点 `:275-281`）：`ACTION_POINT_LOCK`/`ACTION_POINT_EXPORT` 分支先由 `params`（point_type/city/project...）解析为目标 `media_resource_id`（经 `media_resources` 查询，必要时先调一次 ETL/查询接口；对话态下可由助手让用户选定具体点位），再转交 `booking_service`。
- `ToolResult` 字段：`demo` 由 `True` 改为 `False`；`data` 含真实 `booking_no`/`status`/`expire_at`。

**调用 booking_service 方式**：`lock_point` 为 `async def`，内部 `async with AsyncSessionLocal() as db:` 调 `booking_service.create_booking(db, ...)`。失败回滚并保留审计（沿用现有 `write_audit`，`demo` 置 False）。

**接入说明（待明确#A）**：对话里用户通常说"朝阳区XX楼盘门禁点位"，需先把自然语言选择映射到**唯一** `media_resource_id`。P0 建议：助手先返回候选点位列表（复用现有 point_query），用户确认后拿到 `media_resource_id` 再锁；或直接锁"该条件下第一个可用点位"。具体 UX 由前端/助手层定（见 §8 待明确）。

---

## 10. P0-6 · 到期释放 cron

**方案**：APScheduler（新增轻依赖，适配现有 FastAPI）。`app/tasks/scheduler.py` 在 `main.py` `startup` 启动 `BackgroundScheduler`，每 `BOOKING_RELEASE_CRON_SECONDS`（默认 60s）跑一次 `release_expired_bookings()`（`app/tasks/booking_release.py`）。

```python
# app/tasks/booking_release.py（核心）
async def release_expired_bookings() -> int:
    now = datetime.now(timezone.utc)
    async with AsyncSessionLocal() as db:
        rows = (await db.execute(
            select(Booking).where(Booking.status == 'LOCKED', Booking.expire_at < now)
        )).scalars().all()
        for b in rows:
            b.status = 'EXPIRED'
            b.updated_at = now
            # 释放 Redis 层②锁（best-effort）
            await distributed_lock.release(b._lock_key(), token="*")
        await db.commit()
    return len(rows)
```
- 释放语义：`LOCKED` 且 `expire_at` 过期 → `EXPIRED`，档期立即恢复可用（CT-02）；同时 `DEL` 对应 Redis 锁键。
- 备选：独立脚本 `python -m app.tasks.booking_release` 由 OS 计划任务（Windows 任务计划/Linux cron）每分钟调用，逻辑同上（同一函数，sync 包装）。
- 监控：释放计数可写入未来经营大盘（P2）。

---

## 11. P0-7 · CT 超卖压测门禁（CT-01~CT-06）

所有用例置于 `tests/test_booking_ct.py`，用 pytest 并发 / 直插 SQL 实现。通过标准 = 断言全部命中。

| 编号 | 目的 | 压测方式 | 预期断言 | 通过标准 |
|---|---|---|---|---|
| **CT-01** | 同一点位百并发锁位仅 1 成功 | pytest：`asyncio.gather` 100 个 `create_booking`（同一 `media_resource_id`+档期，不同 `idempotency_key`），`SELECTED→LOCKED` | 恰好 1 个返回 200 LOCKED，其余 409（POINT_ALREADY_LOCKED / PROTECTION_RULE_VIOLATED）；DB 中该点位 LOCKED 仅 1 行 | 成功数 == 1，无 2 行重叠 LOCKED |
| **CT-02** | 锁位到期 cron 自动释放 | 插入 LOCKED，`expire_at` 设为过去；跑 `release_expired_bookings()` | 该行 `status` 变 `EXPIRED`；随后同档期可再锁位成功（200） | EXPIRED 且二次锁位可用 |
| **CT-03** | 幂等键去重 | 同一 `idempotency_key` 连续发 2 次 `create_booking` | 两次返回同一 `booking_no`，DB 仅 1 行 | 单号一致、行数 == 1 |
| **CT-04** | 绕过应用层直插重叠 LOCKED 触发 23P01 | 直连 PG `INSERT` 一条与已有 LOCKED 同点位+重叠档期+status=LOCKED | 抛出 `exclude` 冲突（SQLSTATE `23P01`），插入被拒 | 异常码 == 23P01 且 0 行写入 |
| **CT-05** | 进程强杀无脏数据 | 在 `create_booking` 事务提交前 `os.kill` / 注入异常（模拟 crash） | 事务回滚，DB 无半截 LOCKED 行；Redis 锁由 PX 过期回收 | 无孤儿行、无残留 Redis 锁（≤PX 后） |
| **CT-06** | 四层防护下并发混合操作最终一致性 | 混合并发：锁/续期/释放/查询 同点位不同档期 + 同档期，跑 `release_expired_bookings` 穿插 | 任意时刻同点位 LOCKED/PUBLISHED 档期区间互不重叠；超卖率 == 0 | 全量扫描无重叠对 |

> 补充第 6 条即 CT-06（混合最终一致性）。覆盖：并发、到期、幂等、DB 兜底、崩溃安全、混合一致性——六维门禁齐全。

---

## 12. 程序调用流程（时序图：成功 / 超卖被拒 / 到期释放）

### 12.1 锁位成功路径（简化）
沿用 §8 时序：层①无冲突 → 层②取锁 → 层③悲观锁 → 层④INSERT LOCKED 成功 → commit → 释放 Redis 锁 → 返回 `booking_no`。

### 12.2 超卖被拒路径（简化）
任意一层拦截（示例层④）：层①查到既有 LOCKED → 直接 409；或层④ DB 排他抛 `23P01` → rollback → 释放 Redis 锁 → 返回 409 `PROTECTION_RULE_VIOLATED`，DB 零残留。

### 12.3 到期释放路径
```mermaid
sequenceDiagram
    autonumber
    participant SCH as APScheduler(60s)
    participant JOB as release_expired_bookings
    participant PG as PostgreSQL
    participant R as Redis
    SCH->>JOB: trigger
    JOB->>PG: SELECT bookings WHERE status='LOCKED' AND expire_at<now
    PG-->>JOB: 过期 LOCKED 列表
    loop 每个过期 booking
        JOB->>PG: UPDATE status='EXPIRED'
        JOB->>R: DEL qinglin:lock:booking:{mr}:{start}:{end}
    end
    JOB->>PG: COMMIT
    JOB-->>SCH: 释放 N 条
```

---

## 13. 任务列表（有序、含依赖，给工程师寇豆码）

> 按实现顺序排列；T 编号供排期。

1. **T1 基础设施**（无依赖）：在 `requirements.txt` 启用 `asyncpg` + `alembic`；新增 `app/core/exceptions.py`（错误码）；`config.py` 加 `BOOKING_LOCK_PX_MS`/`BOOKING_RELEASE_CRON_SECONDS`；建立 Alembic `alembic.ini` + `migrations/env.py`（async）。
2. **T2 模型与迁移**（依赖 T1）：`app/models/booking.py` 定义 `Booking`/`LockTierConfig`/`MediaLevelRule` + 枚举；`models/__init__.py` 纳入；编写迁移 `0001_booking.py`（§5 DDL + 种子）。执行迁移验证 `23P01` 约束可用。
3. **T3 ETL 与派生**（依赖 T2）：`app/services/level_rule.py`（`derive_level`）+ `app/services/etl_media.py`（读 SQLite→upsert PG，幂等）；跑一次全量 ETL，校验 `media_resources.level` 派生正确、行数对齐。
4. **T4 分布式锁**（依赖 T1）：`app/core/distributed_lock.py`（redis.asyncio SET NX PX + token 释放 + 上下文管理器）。
5. **T5 业务服务**（依赖 T2/T3/T4）：`app/services/booking_service.py`——预检、四层防护编排、续期（受 `lock_tier_config` 约束）、释放、取消、timeline、幂等。
6. **T6 Schemas 与路由**（依赖 T5）：`app/schemas/booking.py` + `app/routers/bookings.py`（PRD §4.1 全端点）；`main.py` 注册路由。
7. **T7 到期释放**（依赖 T2/T4）：`app/tasks/booking_release.py` + `app/tasks/scheduler.py`；`main.py` startup 启动 APScheduler。
8. **T8 助手升级**（依赖 T5/T6）：改 `sale_media.py` 的 `lock_point`/`export_point` 调真实 `booking_service`；`routes.py:275-281` 接入解析 `media_resource_id`；`submit_report` 保留演示态。
9. **T9 测试与验收**（依赖 T2~T8）：`tests/test_etl_media.py` + `tests/test_booking_ct.py`（CT-01~CT-06）；本地起 PG/Redis 跑通六门禁；提交 QA 严过关。

---

## 14. 依赖包列表（标注新增）

| 包 | 状态 | 用途 |
|---|---|---|
| `fastapi` / `uvicorn` / `pydantic` / `pydantic-settings` | 已有 | Web 框架 |
| `SQLAlchemy>=2.0` | 已有 | ORM（新增 async 引擎） |
| **`asyncpg`** | **新增**（取消注释） | PG 异步驱动 |
| **`alembic`** | **新增**（项目级配置，venv 已有） | 迁移 |
| `redis>=5.0.0` | 已有 | 分布式锁（`redis.asyncio`） |
| `psycopg2-binary` | 可选 | 若 ETL 用同步写 PG（asyncpg 已够，可不加） |
| **`APScheduler`** | **新增** | 到期释放定时任务 |
| `pytest` / `pytest-asyncio` | 新增（测试） | CT 压测 |

---

## 15. 共享知识（跨文件约定）

- **命名**：代码标识符一律 `qinglin`（模块 `qinglin_assistant`、服务 `booking_*`、`media_level_rule` 等）；磁盘 SQLite 文件名保持 `qinlin_local.db`、SQLite 表名**保持原样不动**（仅读取）。
- **铁律**：全项目禁止「亲邻」字眼，统一「青柠」/ `qinglin`。文档、日志、UI 文案同此。
- **错误码规范**（`app/core/exceptions.py` 统一抛出，HTTP 映射）：
  - `POINT_ALREADY_LOCKED` → 409（层①/③预检冲突）
  - `PROTECTION_RULE_VIOLATED` → 409（层④排他冲突 / 23P01 包装）
  - `LOCK_QUOTA_EXCEEDED` → 422（续期次数用尽）
  - `BOOKING_NOT_FOUND` → 404
  - `IDEMPOTENT_DUPLICATE` → 200（CT-03，返回既有单）
  - `OFFLINE_OPERATION_FORBIDDEN` → 503
- **时区**：所有 `TIMESTAMPTZ` 以 **UTC** 存储；`lock_start`/`lock_end` 为本地营业日（Asia/Shanghai）的**日历 DATE**，含端点（`daterange(...,'[]')`）。`expire_at` 由 UTC 计算。
- **幂等键格式**：默认 `qlbk::{role}::{session_id}::{media_resource_id}::{lock_start}::{lock_end}`；允许客户端显式传入覆盖（CT-03）。`idempotency_key` 列 UNIQUE。
- **Redis 锁键**：`qinglin:lock:booking:{media_resource_id}:{lock_start}:{lock_end}`，`PX=BOOKING_LOCK_PX_MS`(5000)，value=随机 token（释放时校验防误删）。
- **存储分治**：PG=`ai_adplacer` SSOT；SQLite 只读；Redis 仅锁。绝不跨库 join、绝不写 SQLite。

---

## 16. 待明确事项（仅剩真问题，不含已拍板项）

1. **【UX】对话选择 → `media_resource_id` 绑定方式**（§9 待明确#A）：用户自然语言选点后，如何确定唯一 `media_resource_id`？建议助手先返回候选列表由用户确认，或直接锁"条件下首个可用点位"。需前端/助手层定 UX，不影响 booking 后端。
2. **【决策】全量 async 化 vs 仅 booking 模块 async**：本设计采用"同 Base + 并行 async 引擎"最小化改动；若工程判断整体迁移更优，需评估现有同步路由（`db_api`/`pdooh_*` 等）的改造成本。
3. **【数据】库存 discrepancy 校准**（PRD §0 / 待确认#3）：缺失表（电梯框架/梯影/城市资源索引）与 level 列缺失，是"本地副本不全"还是"数据源已变"？决定 ETL 上游范围与未来 level 派生源（当前按 6 表 + 类型/城市映射派生，已可交付 P0）。
4. **【语义】`lock_end` 边界**（PRD 待确认#5）：`end_date` 为"最后展示日"还是"次日起释放"？本设计统一为**含端点最后展示日**（`daterange(...,'[]')`），预检与约束同口径；如需"次日释放"改为 `daterange(start, end+1, '[)')`，待 Tom 最终确认。
5. **【参数】Redis 锁 PX 与事务时长匹配**（PRD 待确认#4）：本设计默认 5000ms（3–5s 区间），可按实测 DB 事务 P99 调整 `BOOKING_LOCK_PX_MS`。
6. **【范围】报备真实化时机**：P0 保留 `submit_report` 演示态（已拍板），真实化列入 P1-6（接 CRM）。无需 P0 决策。

---

## 17. 设计要点总结

本设计将青柠助手"锁点/导点"从演示态升级为**真实物理防超卖锁位**：以 PostgreSQL `ai_adplacer` 为 SSOT，通过 **ETL 归一化**（方案 A）把只读 SQLite 6 表点位清洗进 `media_resources` 并**派生 level**（类型×城市可配置映射，核心城区+1 档封顶 A++）；Booking 实体引用 `media_resources.id`，状态机 7 态（SELECTED/LOCKED/PUBLISHED/RELEASED/EXPIRED/CANCELLED/TERMINATED），并以 `btree_gist` + `EXCLUDE` 排他约束作为**最后防线**（绕过应用层直插重叠触发 23P01）。锁位走**四层防护**（接口预检 → Redis `SET NX PX` 分布式锁 → DB 悲观锁 `FOR UPDATE ORDER BY id` → DB 排他约束），五档锁位参数（A++ 10/1/5、A+ 7/1/3、A 7/1/3、B 3/1/2、C 3/0/0）可后台配置；到期由 APScheduler 每 60s 扫描 `LOCKED` 过期自动释放。青柠助手 `sale_media.py` 的锁点/导点改调真实 `booking_service`（报备保留演示态），返回真实 `booking_no`、`demo:false`。交付物含完整 DDL、mermaid 状态机/时序图、文件清单、有序任务列表（T1–T9，含依赖）、CT-01~CT-06 六维压测门禁与共享知识约定，工程师可零追问开工。

**剩余待明确项**（不影响 P0 开工，仅 UX/语义细化）：① 对话选点→`media_resource_id` 绑定 UX；② 全量 async 化 vs 仅模块 async 的最终取舍；③ 库存缺失表/level 缺失的数据源校准；④ `lock_end` 端点语义（本设计按含端点实现）；⑤ Redis 锁 PX 与事务时长实测微调。报备真实化已明确留待 P1-6。
