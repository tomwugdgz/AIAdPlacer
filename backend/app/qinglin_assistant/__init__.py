"""青柠智能对话助手（qinglin_assistant）增量模块。

多角色（销售 / 媒介 / 工程 / 商业开发）对话入口，作为 AIAdPlacer 对外智能对话的统一入口。
核心能力全部复用既有地基，禁止重造：

- ``app.db_dao``：qinlin_local.db 真实点位 / 客户数据查询（知识库真查）
- ``app.services.ollama_client``：本地 Ollama LLM 客户端
- ``app.services.tencent_map``：腾讯地图地理编码 / POI 检索
- ``app.common``：统一日志、错误处理、请求 ID

三条交付决策（用户拍板）：
1. LLM = 兼容抽象层：默认本地 Ollama，env 可切 OpenAI 兼容云端。
2. 垂直切片：知识库真查 + 文档生成走真实链路；报备 / 锁点 / 导点等
   操作类走「框架 + 模拟」，返回体必须带 ``demo: true`` 并标注「演示态」。
3. 真数据 + 模拟操作：查询走真实 DB，操作类模拟。

命名约定：模块目录 / 类 / 注释 / 文案统一「青柠 / qinglin」。
唯一例外：``qinlin_local.db`` 文件名保持原样（既有资产，改名会连锁破坏 db_dao 与其他模块）。
"""
