# 增量 PRD：青柠智能对话助手模块

## 1. 变更目标
在 AIAdPlacer(pDOOH) 上叠加以 LLM 为推理核心的「多角色对话入口」，复用既有 Ollama/MCP/知识库地基，先跑通真实链路垂直切片。

## 2. 模块命名与包规划
新建 `backend/app/qinglin_assistant/`（与现有 qinglin/青柠 demo 区分；路径相对 AIAdPlacer 后端，与 `services/`、`api/`、`agents/` 同级）：
- `rbac/` 四角色校验 + 跨人查询拦截 + 数据脱敏(138****1234)
- `llm/` provider 抽象层（封装 `OllamaClient`，env 可切 OpenAI/Claude/DashScope 等兼容 OpenAI 协议云端）
- `memory/` 会话级跨轮记忆
- `intent/` 意图识别 + 工具编排核心
- `tools/` `call_api_sale/media/engineer/developer` + `web_search`/`map_*`/`check_permission`/`get_user_role_skill`
- `skills/` docx/xlsx/pptx/pdf/tos-file-access 注册与管理
- `workflows/` 点位/销售/媒介/文档（操作类模拟并标注「演示态」）
- `sandbox/` `bash_tool` 命令黑名单 + 资源限制 + 沙箱隔离
- `api/` `/api/v2/assistant/chat` 等路由

## 3. 用户故事
- 销售(sale)：用自然语言查点位并生成报备跟进文档，快速响应客户。
- 媒介(media)：查询并导出点位、申请锁点，协同排期。
- 工程(engineer)：经助手调工程接口且受 RBAC 拦截，避免越权。
- 决策层(developer)：操作类显为演示态、真实链路可审计，放心上线。

## 4. 需求池
**P0（垂直切片必做）**：① provider 抽象 LLM 核心（默认 Ollama 可切云端）② RBAC 四角色+权限校验+脱敏 ③ 意图识别+工具编排核心 ④ 记忆系统(session 级) ⑤ 知识库真查（青柠真实 DB 点位，接真实库）⑥ 文档生成技能（docx/xlsx 至少跑通）⑦ 业务 API 工具骨架 `call_api_*` ⑧ 安全沙箱（bash_tool 黑名单+限制）⑨ 助手 API 路由 `/api/v2/assistant/chat` ⑩ Demo 页对话面板（角色选择+消息框+调助手 API）

**P1（框架+模拟）**：销售操作工作流（报备/跟进，模拟标注）；媒介操作工作流（锁点/导点，模拟标注）；`web_search` 辅助工具(stub)

**P2（文档）**：README 章节；架构图；与现有 A2A/MCP 关系说明

## 5. 验收标准（DoD）
- 助手 `/api/v2/assistant/chat` 接收 `(role, session_id, message)` 返回结构化回复
- RBAC 拦截越权（如 engineer 调 sale 接口被拒）
- 知识库真查返回真实点位（青柠 DB）
- 文档生成产出真实 docx/xlsx 文件
- 模拟操作明确返回「演示态」标识，不伪装写库
- Demo 页可切换角色并对话
- 现有 A2A/MCP 与其他子系统测试不破

## 6. 待确认问题
1. provider 抽象层是否需按角色并行选模型（一次请求多 model）？
2. 记忆系统 session 级即可，还是需持久化跨会话长期记忆（P0 范围界定）？
3. 演示态模拟操作是否需审计日志留痕，以满足「可审计」决策要求？
