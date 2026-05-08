# AI智能投放系统 (AIAdPlacer) CPS 2.0

> **5C × 5V 社区媒体数字化平台** — 多Agent协同的智能广告投放与效果归因系统

基于腾讯地图地域归因分析，整合线上线下媒体资源，通过四大AI Agent（人群洞察/智能排期/动态创意/效果归因）实现社区媒体全链路数字化。
<img width="1254" height="1128" alt="image" src="https://github.com/user-attachments/assets/e1acfff5-49f8-47f2-a33c-2adaf8dd30de" />

---

## 5C × 5V 框架

### 5C 社区框架
| 维度 | 含义 | 系统实现 |
|------|------|---------|
| **Context** 场景上下文 | LBS位置+时段+客流量 | QADN点位数据、商圈类型、高峰时段 |
| **Community** 社区人群 | 微细分群体画像 | KMeans聚类、友盟数据融合、兴趣标签 |
| **Content** 内容创意 | 场景适配创意生成 | AIGC文案、DCO动态创意优化、多模态 |
| **Connection** 社区链接 | 线上线下跨端连接 | Cookie-ID+设备指纹、多触点归因 |
| **Commerce** 商业转化 | ROI最大化与分成 | CPS 2.0动态分成、实时ROI看板 |

### 5V 数据特性
| 维度 | 含义 | 系统实现 |
|------|------|---------|
| **Volume** 数据体量 | 百万级曝光/行为数据 | PostgreSQL + pandas聚合分析 |
| **Velocity** 数据速度 | 实时归因、分钟级优化 | FastAPI异步处理 + Redis缓存 |
| **Variety** 数据类型 | 多源数据融合 | QADN+天工智投+亲邻APP+友盟 |
| **Value** 数据价值 | CPM<9元、ROI最大化 | FM模型预估+约束优化求解 |
| **Veracity** 数据真实性 | 跨端身份验证 | Cookie-ID+设备指纹匹配率68% |

### 5C × 5V 矩阵
```
          Volume      Velocity     Variety       Value       Veracity
Context   海量位置    实时场景     LBS+天气      精准场景    位置验证
Community 百万画像    动态聚类     多平台人群    高价值识别  身份去重
Content   千组创意    实时DCO      文本+图片     高CTR创意   A/B验证
Connection 全链触点   实时匹配     Cookie+指纹   高转化链路  跨端验证
Commerce  全量转化    实时ROI      线上+线下     ROI最大化   归因验证
```

---

## 核心功能

### 🎯 媒体资源管理
- 线下资源：社区广告、单元门广告、户外大屏、电梯广告、公交站牌的地理位置录入
- 线上资源：网站/app广告位、社交媒体账号
- 资源标签：按地域、类型、价格、覆盖人群分类
- 库存管理：实时可用状态追踪

### 🤖 CPS 2.0 多Agent协同
- **人群洞察Agent**: LBS+友盟数据融合，KMeans聚类动态分群
- **智能排期Agent**: FM线性模型+deepMCP，约束优化求解最优排期
- **动态创意Agent**: AIGC生成社区场景适配素材，DCO动态创意优化
- **效果归因Agent**: Cookie-ID+设备指纹跨端归因，实时ROI看板
- **统一编排Agent**: LangGraph状态机，规划→执行→反思循环

### 🗺️ 腾讯地图集成
- 地理编码：地址转坐标
- POI搜索：查找广告位周边商圈
- 热力图可视化：投放效果地理分布
- 距离矩阵计算

### 📈 归因分析引擎
- **地域归因**: 腾讯地图热力图展示各区域效果
- **多触点归因**: 首次触点/最终触点/线性归因/时间衰减
- **时空归因**: 时间×地理二维归因矩阵
- **转化漏斗**: 曝光→点击→转化的完整路径

### 📊 CPS 2.0 动态分成
| ROI区间 | 分成比例 | 说明 |
|---------|---------|------|
| ROI < 100% | 10% | 基础服务，无效果奖励 |
| 100% ≤ ROI < 200% | 18% | 达标投放，基础奖励 |
| 200% ≤ ROI < 300% | 25% | 优秀投放，效果奖励 |
| ROI ≥ 300% | 30% | 卓越投放，最高分成 |

---

## 技术架构

| 层级 | 技术 | 说明 |
|------|------|------|
| 后端 | Python + FastAPI | 高性能API，异步支持 |
| Agent | LangGraph + LangChain | 多Agent协同编排 |
| RAG | ChromaDB + text2vec | Agent驱动知识库 |
| 数据库 | PostgreSQL | 关系型数据存储 |
| 缓存 | Redis | 实时数据缓存 |
| 地图 | 腾讯地图 JSAPI GL + WebService API | 地理位置服务 |

---

## 快速开始

### 环境要求
- Python 3.13+
- PostgreSQL 15+
- Redis 7+

### 安装依赖
```bash
cd backend
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 配置环境变量
创建 `backend/.env` 文件（参考 `.env.example`）：
```env
DATABASE_URL=postgresql://user:password@127.0.0.1:5432/ai_adplacer
REDIS_URL=redis://127.0.0.1:6379/0
TENCENT_MAP_KEY=your_tencent_map_key
LLM_API_KEY=your_llm_api_key
LLM_API_URL=your_llm_api_url
```

### 启动服务
```bash
cd backend
python run.py
```

服务启动后访问：
- API文档：http://127.0.0.1:5002/docs
- CPS 1.0 演示：http://127.0.0.1:5002/demo
- CPS 2.0 演示：http://127.0.0.1:5002/cps2-demo

---

## API接口

### v1 基础API
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/media` | 媒体资源列表 |
| POST | `/api/v1/media` | 创建媒体资源 |
| GET | `/api/v1/campaigns` | 投放计划列表 |
| POST | `/api/v1/campaigns` | 创建投放计划 |
| GET | `/api/v1/map/geocode` | 地理编码 |
| GET | `/api/v1/attribution/geo` | 地域归因 |
| GET | `/api/v1/attribution/funnel` | 转化漏斗 |

### v2 Agent API
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v2/agents/execute` | 执行完整Agent工作流 |
| GET | `/api/v2/agents/audience-insight` | 人群洞察分析 |
| POST | `/api/v2/agents/schedule` | 智能排期生成 |
| POST | `/api/v2/agents/creative` | 动态创意生成 |
| GET | `/api/v2/agents/attribution` | 效果归因分析 |
| GET | `/api/v2/rag/knowledge` | RAG知识库检索 |

---

## 数据模型

### 核心数据表
- `media_resources` — 媒体资源（线下+线上）
- `campaigns` — 投放计划
- `campaign_media` — 计划与媒体关联
- `placements` — 投放执行记录
- `conversions` — 转化数据（含跨端匹配）

### 数据源接入（5V Variety）
| 数据源 | 类型 | 用途 |
|--------|------|------|
| QADN点位 | LBS位置+客流量 | Context场景上下文 |
| 天工智投 | 点位库存+档期 | Commerce商业转化 |
| 亲邻APP | 用户行为序列 | Connection社区链接 |
| 友盟画像 | 人群年龄/兴趣 | Community社区人群 |

---

## 项目结构
```
AIAdPlacer/
├── backend/
│   ├── app/
│   │   ├── api/           # API路由
│   │   │   ├── routes.py      # v1基础路由
│   │   │   ├── attribution.py # 归因分析路由
│   │   │   ├── agents.py      # v2 Agent路由
│   │   │   └── schemas.py     # 数据模型定义
│   │   ├── agents/        # CPS 2.0 Agent模块
│   │   │   ├── orchestrator.py      # 统一编排Agent
│   │   │   ├── audience_insight.py  # 人群洞察Agent
│   │   │   ├── smart_schedule.py    # 智能排期Agent
│   │   │   ├── dynamic_creative.py  # 动态创意Agent
│   │   │   └── attribution.py       # 效果归因Agent
│   │   ├── models/        # 数据库模型
│   │   │   └── __init__.py    # SQLAlchemy模型
│   │   ├── services/      # 业务逻辑
│   │   │   ├── tencent_map.py     # 腾讯地图服务
│   │   │   ├── attribution_engine.py  # 归因引擎
│   │   │   ├── ai_recommender.py      # AI推荐
│   │   │   ├── rag_kb.py              # RAG知识库
│   │   │   ├── llm_client.py          # LLM客户端
│   │   │   └── mock_data.py           # 模拟数据源
│   │   ├── config.py      # 配置管理
│   │   └── main.py        # 应用入口
│   ├── data/knowledge/    # RAG知识库文档
│   ├── requirements.txt
│   └── run.py
├── frontend/              # 前端（待开发）
├── ARCHITECTURE.md        # 5C×5V架构设计文档
├── docker-compose.yml     # Docker编排
├── cps2-demo.html         # CPS 2.0演示页面
└── business-proposal-cps2.html  # 商业方案
```

---

## 演示数据结果

基于50条投放记录、139条转化数据的分析：

| 指标 | 数值 |
|------|------|
| 总曝光量 | 1,284,641 次 |
| 总点击量 | 60,119 次（CTR 4.68%） |
| 总转化量 | 2,279 次（CVR 3.79%） |
| 总投放成本 | ¥82,500 |
| 平均转化成本 | ¥36.20 |
| ROI最高区域 | 微信朋友圈 (3.62%) |

---

## 部署方案

### Docker Compose
```bash
docker-compose up -d
```

### 手动部署
1. 创建PostgreSQL数据库 `ai_adplacer`
2. 启动Redis服务
3. 安装后端依赖并启动
4. 配置Nginx反向代理

---

## 后续规划
1. 接入真实广告平台API数据
2. 完善API认证机制（JWT/OAuth）
3. 引入日志系统（结构化日志+错误追踪）
4. 添加单元测试和集成测试
5. 多租户SaaS化部署
6. 移动端适配

---

## 许可证

MIT License
