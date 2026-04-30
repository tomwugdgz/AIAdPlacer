# AI智能投放系统 (AIAdPlacer)

基于腾讯地图地域归因分析的智能广告投放决策平台，整合线上线下媒体资源，提供AI驱动的投放策略推荐与效果归因分析。

---

## 核心功能

### 🎯 媒体资源管理
- 线下资源：社区广告、单元门广告、户外大屏、电梯广告、公交站牌的地理位置录入
- 线上资源：网站/app广告位、社交媒体账号
- 资源标签：按地域、类型、价格、覆盖人群分类
- 库存管理：实时可用状态追踪

### 📊 投放计划管理
- 计划创建：选择媒体资源、设置预算、时间、目标人群
- 智能排期：AI推荐最佳投放时段和组合
- 预算分配：自动优化各渠道预算比例
- 状态追踪：执行中/已完成/已暂停

### 🗺️ 腾讯地图集成
- 地理编码：地址转坐标
- POI搜索：查找广告位周边商圈
- 热力图可视化：投放效果地理分布
- 距离矩阵计算

### 📈 归因分析引擎
- **地域归因**：腾讯地图热力图展示各区域效果
- **多触点归因**：首次触点/最终触点/线性归因/时间衰减
- **时空归因**：时间×地理二维归因矩阵
- **转化漏斗**：曝光→点击→转化的完整路径

### 🤖 AI智能推荐
- 基于历史数据分析最佳媒体组合
- 地域特征分析与商圈评估
- 预算分配优化建议
- 行业投放策略推荐

---

## 技术架构

| 层级 | 技术 | 说明 |
|------|------|------|
| 后端 | Python + FastAPI | 高性能API，异步支持 |
| 前端 | HTML + 腾讯地图JSAPI GL | 现代化管理界面 |
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
编辑 `backend/.env` 文件：
```env
DATABASE_URL=postgresql://user:password@127.0.0.1:5432/ai_adplacer
REDIS_URL=redis://127.0.0.1:6379/0
TENCENT_MAP_KEY=7HKBZ-HQBEM-XS56X-6DBAT-ITXUZ-IDFNG
```

### 启动服务
```bash
cd backend
python run.py
```

服务启动后访问：
- API文档：http://127.0.0.1:5002/docs
- 演示页面：http://127.0.0.1:5002/demo

---

## API接口

### 媒体资源
- `GET /api/media` - 获取媒体资源列表
- `POST /api/media` - 创建媒体资源
- `GET /api/media/{id}` - 获取媒体资源详情
- `PUT /api/media/{id}` - 更新媒体资源
- `DELETE /api/media/{id}` - 删除媒体资源

### 投放计划
- `GET /api/campaigns` - 获取投放计划列表
- `POST /api/campaigns` - 创建投放计划
- `POST /api/campaigns/{id}/activate` - 激活投放计划
- `POST /api/campaigns/{id}/pause` - 暂停投放计划

### 腾讯地图
- `GET /api/map/geocode?address=xxx&city=xxx` - 地址转坐标
- `GET /api/map/reverse-geocode?lat=xxx&lng=xxx` - 坐标转地址
- `GET /api/map/search-poi?keyword=xxx&lat=xxx&lng=xxx` - POI搜索

### 归因分析
- `GET /api/attribution/geo?campaign_id=xxx` - 地域归因
- `GET /api/attribution/multi-touch?model=linear` - 多触点归因
- `GET /api/attribution/spatio-temporal` - 时空归因
- `GET /api/attribution/funnel` - 转化漏斗

### AI推荐
- `GET /api/ai/recommend-media?budget=10000&lat=xxx&lng=xxx` - 媒体推荐
- `GET /api/ai/strategy-suggestion?industry=retail` - 策略建议

---

## 数据模型

### 媒体资源表 (media_resources)
- 基础信息：名称、类型、分类
- 地理位置：经纬度、地址、覆盖半径
- 商业信息：日均价格、日均曝光量
- 状态管理：可用/已预订/维护中

### 投放计划表 (campaigns)
- 计划信息：名称、描述、预算
- 时间设置：开始日期、结束日期
- 目标设定：目标人群标签
- AI推荐：智能推荐结果

### 投放记录表 (placements)
- 关联信息：计划ID、媒体ID
- 效果数据：曝光、点击、转化
- 成本信息：投放成本
- 地理位置：经纬度

### 转化数据表 (conversions)
- 用户信息：用户ID、转化类型
- 价值信息：转化价值
- 归因信息：触点顺序、归因模型
- 地理位置：转化发生位置

---

## 归因分析算法

### 地域归因模型
```
ROI = 转化价值 / 投放成本
按地理位置聚合，计算各区域ROI排名
```

### 多触点归因模型
| 模型 | 说明 |
|------|------|
| 首次触点 | 第一次接触的媒体获得全部转化权重 |
| 最终触点 | 最后一次接触的媒体获得全部转化权重 |
| 线性归因 | 所有接触点平均分配转化权重 |
| 时间衰减 | 越接近转化的触点权重越高 |

### 时空归因矩阵
```
时间 × 地理 二维分析
- 时间维度：按日期/时段聚合效果
- 地理维度：按区域聚合效果
- 交叉分析：找出最优时段+区域组合
```

---

## 腾讯地图API集成

### 已配置API Key
```
7HKBZ-HQBEM-XS56X-6DBAT-ITXUZ-IDFNG
```

### 使用场景
1. **地理编码**：录入媒体资源时自动获取坐标
2. **POI搜索**：查找广告位周边商圈和竞品
3. **热力图**：前端展示投放效果地理分布
4. **距离矩阵**：计算媒体资源间的覆盖关系

---

## 项目结构
```
AIAdPlacer/
├── backend/
│   ├── app/
│   │   ├── api/           # API路由
│   │   │   ├── routes.py      # 主要路由
│   │   │   ├── attribution.py # 归因分析路由
│   │   │   └── schemas.py     # 数据模型定义
│   │   ├── models/        # 数据库模型
│   │   │   └── __init__.py    # SQLAlchemy模型
│   │   ├── services/      # 业务逻辑
│   │   │   ├── tencent_map.py    # 腾讯地图服务
│   │   │   ├── attribution_engine.py # 归因引擎
│   │   │   └── ai_recommender.py   # AI推荐
│   │   ├── config.py      # 配置管理
│   │   └── main.py        # 应用入口
│   ├── requirements.txt
│   ├── .env
│   └── run.py
├── frontend/              # 前端（待开发）
├── docker-compose.yml     # Docker编排
└── demo.html              # 演示页面
```

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
2. 机器学习预测模型训练
3. 多租户SaaS化部署
4. 移动端适配
5. A/B测试框架

---

## 许可证

MIT License
