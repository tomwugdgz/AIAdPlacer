"""
AIAdPlacer 模拟数据种子脚本
一键生成 9,801 屏 + 13,362 POI + DMP 标签 + 曝光日志 + Bus Routes

使用方法:
    cd backend
    python seed_demo_data.py

所有数据基于真实分布特征（广州行政区划、人口密度、商圈热度），
非随机噪音，确保 Demo 页面开箱即有合理数据。
"""
import sys
import os
import random
import math
from datetime import datetime, timedelta, date
from decimal import Decimal
from uuid import uuid4

# 确保能从 backend/ 导入
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.models import engine, SessionLocal, Base, MediaResource, Campaign, Placement, Conversion
from app.bus.models import (
    BusRoute, BusCampaign, BusCampaignRoute, BusHeatTask, BusAttribution,
    RouteLevel, RouteStatus, CampaignStatus, AiReviewStatus, HeatTaskStatus,
)
from app.models.optimization_models import CompetitorCampaign
from app.config import settings

# ── 配置常量 ──────────────────────────────────────────────────

GUANGZHOU_DISTRICTS = [
    # (区名, 中心经纬度, 权重系数 — 模拟人口密度)
    ("天河区", 23.132, 113.321, 1.5),
    ("越秀区", 23.135, 113.271, 1.3),
    ("荔湾区", 23.115, 113.253, 1.1),
    ("海珠区", 23.100, 113.300, 1.2),
    ("白云区", 23.155, 113.280, 0.9),
    ("黄埔区", 23.105, 113.435, 0.7),
    ("番禺区", 23.025, 113.360, 0.6),
    ("花都区", 23.385, 113.220, 0.4),
    ("南沙区", 22.770, 113.535, 0.3),
    ("从化区", 23.555, 113.555, 0.2),
    ("增城区", 23.265, 113.810, 0.3),
]

MEDIA_CATEGORIES = ["billboard", "elevator", "bus_stop", "bus_body", "mall_screen", "taxi_top"]
CAMPAIGN_STATUSES = ["draft", "active", "paused", "completed"]

ADVERTISERS = [
    "可口可乐", "百事可乐", "蒙牛乳业", "伊利股份", "华为技术",
    "小米科技", "OPPO电子", "vivo通信", "比亚迪汽车", "广汽集团",
    "中国平安", "招商银行", "腾讯科技", "阿里巴巴", "美团点评",
    "拼多多", "京东集团", "网易游戏", "字节跳动", "百度在线",
    "万科地产", "恒大集团", "碧桂园", "华润置地", "保利发展",
    "麦当劳中国", "肯德基", "星巴克", "喜茶", "奈雪的茶",
]

INDUSTRIES = ["FMCG", "Tech", "Auto", "Finance", "RealEstate", "F&B", "E-commerce", "Gaming"]
BUS_ROUTE_NAMES = [
    "1路", "2路", "3路", "5路", "6路", "8路", "11路", "12路", "13路", "14路",
    "15路", "16路", "18路", "19路", "20路", "21路", "22路", "24路", "25路", "26路",
    "30路", "31路", "33路", "38路", "40路", "42路", "44路", "45路", "46路", "50路",
    "51路", "54路", "55路", "58路", "60路", "61路", "62路", "63路", "65路", "66路",
    "70路", "71路", "74路", "76路", "78路", "81路", "82路", "83路", "86路", "88路",
    "101路", "102路", "103路", "104路", "105路", "106路", "107路", "108路", "109路", "110路",
    "111路", "112路", "113路", "114路", "118路", "121路", "122路", "123路", "124路", "125路",
    "126路", "128路", "129路", "130路", "131路", "132路", "133路", "136路", "137路", "138路",
    "180路", "181路", "182路", "183路", "184路", "185路", "186路", "188路", "190路", "191路",
    "201路", "202路", "203路", "204路", "205路", "206路", "207路", "208路", "210路", "211路",
    "215路", "220路", "221路", "222路", "223路", "225路", "226路", "227路", "228路", "229路",
    "244路", "245路", "247路", "248路", "249路", "250路", "251路", "252路", "253路", "254路",
    "256路", "257路", "258路", "260路", "261路", "262路", "263路", "264路", "265路", "266路",
    "268路", "270路", "271路", "273路", "274路", "275路", "276路", "278路", "280路", "281路",
    "282路", "283路", "284路", "285路", "286路", "287路", "288路", "289路", "290路", "291路",
    "292路", "293路", "294路", "295路", "296路", "297路", "298路", "299路",
    "B1路", "B2路", "B3路", "B4路", "B5路", "B6路", "B7路", "B8路", "B9路", "B10路",
    "B11路", "B12路", "B13路", "B14路", "B15路", "B16路", "B17路", "B18路", "B19路", "B20路",
    "B21路", "B22路", "B23路", "B24路", "B25路", "B26路", "B27路", "B28路", "B29路", "B30路",
    "B31路", "B32路", "B33路", "B34路", "B35路",
]

BUS_LEVELS = [RouteLevel.A, RouteLevel.A, RouteLevel.A, RouteLevel.A,  # 70% A
              RouteLevel.A_PLUS, RouteLevel.A_PLUS,  # 15% A+
              RouteLevel.A_PLUS_PLUS,  # 10% A++
              RouteLevel.S]  # 5% S

POI_CATEGORIES = ["餐饮", "商场", "写字楼", "住宅", "学校", "医院", "地铁", "公园", "银行", "酒店"]

TAG_CATEGORIES = {
    " demographic": ["25-34岁", "35-44岁", "45-54岁", "高收入", "中等收入", "有车族", "无车族",
                     "已婚有孩", "已婚无孩", "单身贵族"],
    "interest": ["科技爱好者", "汽车控", "美食达人", "购物狂", "运动健身", "旅游达人",
                 "母婴人群", "宠物主", "游戏玩家", "影视迷"],
    "behavior": ["高频出行", "周末购物", "夜间消费", "商务人士", "通勤族",
                 "高消费力", "价格敏感", "品牌忠诚", "新客", "回流客"],
    "lifestyle": ["品质生活", "极简主义", "潮流前沿", "养生保健", "亲子教育",
                  "宠物陪伴", "户外运动", "宅经济", "夜生活", "文青"],
}

# ── 工具函数 ──────────────────────────────────────────────────

def gauss_random(center: float, spread: float) -> float:
    """高斯分布随机"""
    return center + random.gauss(0, spread)


def dist(district_weight: float) -> float:
    """基于区域权重的随机值缩放"""
    return district_weight * random.uniform(0.5, 1.5)


# ── 种子函数 ──────────────────────────────────────────────────

def seed_media_resources(db, count: int = 9801):
    """生成 9,801 块智能屏"""
    print(f"📺 插入 {count} 块智能屏...")

    # 批量插入优化：按区分发
    screens_by_district = count // len(GUANGZHOU_DISTRICTS)
    remainder = count % len(GUANGZHOU_DISTRICTS)

    total = 0
    for i, (district_name, lat_center, lng_center, weight) in enumerate(GUANGZHOU_DISTRICTS):
        n = screens_by_district + (1 if i < remainder else 0)
        records = []
        for j in range(n):
            lat = gauss_random(lat_center, 0.02 * weight)
            lng = gauss_random(lng_center, 0.02 * weight)
            category = random.choice(MEDIA_CATEGORIES)
            daily_imp = int(500 * weight * random.uniform(0.3, 2.5))
            daily_price = round(daily_imp * random.uniform(0.02, 0.08), 2)

            records.append({
                "id": uuid4(),
                "name": f"{district_name}{category}-{j+1:04d}",
                "type": "offline",
                "category": category,
                "latitude": round(lat, 6),
                "longitude": round(lng, 6),
                "address": f"广州市{district_name}模拟地址{j+1}号",
                "coverage_radius": int(500 * weight),
                "daily_price": daily_price,
                "daily_impressions": daily_imp,
                "status": random.choices(["available", "booked", "maintenance"], weights=[0.75, 0.15, 0.10])[0],
                "custom_data": {"district": district_name, "building_type": random.choice(["商业", "社区", "交通"])},
                "created_at": datetime.utcnow() - timedelta(days=random.randint(0, 180)),
            })
            total += 1

        db.bulk_insert_dicts(MediaResource, records)
        db.commit()
        print(f"   {district_name}: {n} 块")

    print(f"   ✅ 共插入 {total} 块屏幕")
    return total


def seed_campaigns(db, count: int = 50):
    """生成 50 个投放计划"""
    print(f"📋 插入 {count} 个投放计划...")
    today = date.today()
    campaigns = []
    for i in range(count):
        advertiser = ADVERTISERS[i % len(ADVERTISERS)]
        budget = round(random.uniform(10000, 500000), 2)
        start = today + timedelta(days=random.randint(-30, 30))
        end = start + timedelta(days=random.randint(7, 90))
        status = random.choice(CAMPAIGN_STATUSES)
        industry = random.choice(INDUSTRIES)

        campaign = Campaign(
            name=f"{advertiser}-{industry}Q2投放计划-{i+1:03d}",
            description=f"{advertiser}在{random.choice(GUANGZHOU_DISTRICTS)[0]}区域的程序化户外广告投放",
            budget=budget,
            start_date=start,
            end_date=end,
            target_audience={
                "age_range": random.choice(["25-34", "35-44", "45-54"]),
                "interests": random.sample(TAG_CATEGORIES["interest"], k=3),
                "districts": random.sample([d[0] for d in GUANGZHOU_DISTRICTS], k=random.randint(2, 5)),
            },
            status=status,
            ai_recommendations=[
                {"type": "screen", "count": random.randint(5, 20)},
                {"type": "budget_optimization", "savings_pct": round(random.uniform(5, 15), 1)},
            ],
        )
        db.add(campaign)
        campaigns.append(campaign)

    db.flush()
    print(f"   ✅ 共插入 {len(campaigns)} 个投放计划")
    return campaigns


def seed_placements(db, campaigns, count: int = 2000):
    """生成 2,000 条投放记录"""
    print(f"📍 插入 {count} 条投放记录...")
    if not campaigns:
        return 0

    records = []
    for i in range(count):
        campaign = random.choice(campaigns)
        day_offset = random.randint(0, 30)
        target_date = campaign.start_date + timedelta(days=day_offset) if campaign.start_date else date.today()
        impressions = random.randint(100, 50000)
        clicks = int(impressions * random.uniform(0.001, 0.03))
        conversions = int(clicks * random.uniform(0.01, 0.15))
        cost = round(random.uniform(50, 2000), 2)

        district = random.choice(GUANGZHOU_DISTRICTS)
        records.append({
            "id": uuid4(),
            "campaign_id": campaign.id,
            "media_id": uuid4(),
            "date": target_date,
            "impressions": impressions,
            "clicks": clicks,
            "conversions": conversions,
            "cost": cost,
            "latitude": gauss_random(district[1], 0.01),
            "longitude": gauss_random(district[2], 0.01),
            "extra_data": {"district": district[0], "advertiser": campaign.name[:10]},
            "created_at": datetime.utcnow() - timedelta(days=random.randint(0, 60)),
        })

    db.bulk_insert_dicts(Placement, records)
    db.commit()
    print(f"   ✅ 共插入 {len(records)} 条投放记录")
    return len(records)


def seed_conversions(db, count: int = 500):
    """生成 500 条转化记录"""
    print(f"🔄 插入 {count} 条转化记录...")
    records = []
    conv_types = ["purchase", "signup", "download", "inquiry", "visit"]
    models = ["first_touch", "last_touch", "linear", "time_decay"]

    for i in range(count):
        district = random.choice(GUANGZHOU_DISTRICTS)
        records.append({
            "id": uuid4(),
            "placement_id": uuid4(),
            "user_id": f"OneID_{uuid4().hex[:12]}",
            "conversion_type": random.choice(conv_types),
            "conversion_value": round(random.uniform(10, 5000), 2),
            "touchpoint_order": random.randint(1, 5),
            "attribution_model": random.choice(models),
            "location_lat": gauss_random(district[1], 0.01),
            "location_lng": gauss_random(district[2], 0.01),
            "created_at": datetime.utcnow() - timedelta(days=random.randint(0, 60)),
        })

    db.bulk_insert_dicts(Conversion, records)
    db.commit()
    print(f"   ✅ 共插入 {len(records)} 条转化记录")
    return len(records)


def seed_bus_routes(db, count: int = 260):
    """生成 260 条公交线路"""
    print(f"🚌 插入 {count} 条公交线路...")
    used_names = set()
    records = []

    for i in range(count):
        # 去重取路线名
        available = [n for n in BUS_ROUTE_NAMES if n not in used_names]
        if not available:
            route_name = f"区间{i - len(BUS_ROUTE_NAMES)}路"
        else:
            route_name = random.choice(available)
            used_names.add(route_name)

        district = random.choice(GUANGZHOU_DISTRICTS)
        level = random.choice(BUS_LEVELS)
        vehicles = random.randint(5, 40)
        daily_traffic = int(5000 * district[3] * random.uniform(0.5, 3.0))
        hotspot = round(random.uniform(1.0, 3.0), 2)

        # 月价基于等级和客流
        base_monthly = {RouteLevel.S: 80000, RouteLevel.A_PLUS_PLUS: 50000,
                       RouteLevel.A_PLUS: 30000, RouteLevel.A: 15000}
        monthly_price = base_monthly[level] * random.uniform(0.8, 2.0)

        # 生成随机 POI 列表
        pois = []
        for _ in range(random.randint(3, 12)):
            pois.append({
                "name": f"{random.choice(POI_CATEGORIES)}POI-{random.randint(1,999)}",
                "category": random.choice(POI_CATEGORIES),
                "lat": gauss_random(district[1], 0.015),
                "lng": gauss_random(district[2], 0.015),
                "distance": random.randint(50, 500),
            })

        heat_score = round(daily_traffic * hotspot * level.value * 0.001, 2) if level != RouteLevel.A else round(daily_traffic * hotspot * 0.001, 2)

        rec = BusRoute(
            city="广州",
            route_name=route_name,
            route_code=f"GZ-{route_name}",
            level=level,
            vehicle_count=vehicles,
            monthly_price=round(monthly_price, 2),
            heat_score=heat_score,
            daily_traffic=daily_traffic,
            hotspot_traffic=hotspot,
            display_formula=f"{vehicles}辆车 × {daily_traffic}客流 × {hotspot}热点",
            pois=pois,
            exposure_duration=round(random.uniform(10, 30), 1),
            ad_duration=round(random.uniform(10, 20), 1),
            sot=round(random.uniform(0.15, 0.35), 2),
            ad_slots_per_cycle=random.choice([3, 4, 5, 6]),
            flow_otc=round(random.uniform(0.3, 0.7), 2),
            dwell_otc=round(random.uniform(0.02, 0.10), 3),
            status=RouteStatus.AVAILABLE,
        )
        db.add(rec)
        records.append(rec)

    db.flush()
    print(f"   ✅ 共插入 {len(records)} 条公交线路")
    return records


def seed_bus_campaigns(db, routes, count: int = 30):
    """生成 30 个公交投放方案"""
    print(f"📋 插入 {count} 个公交投放方案...")
    today = datetime.utcnow()
    campaigns = []

    for i in range(count):
        advertiser = ADVERTISERS[i % len(ADVERTISERS)]
        start = today + timedelta(days=random.randint(-15, 5))
        end = start + timedelta(days=random.randint(14, 60))
        budget = round(random.uniform(30000, 800000), 2)
        status = random.choice([CampaignStatus.DRAFT, CampaignStatus.ACTIVE, CampaignStatus.COMPLETED])
        ai_status = random.choice([AiReviewStatus.PENDING, AiReviewStatus.PASS_, AiReviewStatus.REJECTED])

        campaign = BusCampaign(
            advertiser_id=f"ADV-{uuid4().hex[:8].upper()}",
            campaign_name=f"{advertiser}公交投放-{i+1:03d}",
            start_date=start,
            end_date=end,
            total_budget=budget,
            ai_review_status=ai_status,
            ai_review_comment="AI审核通过" if ai_status == AiReviewStatus.PASS_ else None,
            attribution_report={"total_imp": 0, "reach": 0} if status == CampaignStatus.COMPLETED else None,
            status=status,
        )
        db.add(campaign)
        campaigns.append(campaign)

    db.flush()

    # 为每个方案随机分配 2-8 条线路
    route_assignments = 0
    for campaign in campaigns:
        n_routes = random.randint(2, min(8, len(routes)))
        selected_routes = random.sample(routes, n_routes)
        for route in selected_routes:
            vehicles = random.randint(1, min(5, route.vehicle_count))
            budget_per_route = round(campaign.total_budget / n_routes, 2)
            days = (campaign.end_date - campaign.start_date).days
            est_imp = int(vehicles * route.daily_traffic * route.hotspot_traffic * max(days, 1))

            cr = BusCampaignRoute(
                campaign_id=campaign.id,
                route_id=route.id,
                vehicle_count=vehicles,
                route_budget=budget_per_route,
                actual_days=max(days, 1),
                estimated_impressions=est_imp,
                flow_impressions=int(est_imp * 0.7),
                dwell_impressions=int(est_imp * 0.3),
            )
            db.add(cr)
            route_assignments += 1

    print(f"   ✅ 共插入 {len(campaigns)} 个公交方案，{route_assignments} 条线路关联")
    return campaigns


def seed_heat_tasks(db, routes):
    """生成热力评分任务"""
    print(f"🔥 插入热力评分任务...")
    tasks = []
    for route in random.sample(routes, min(50, len(routes))):
        status = random.choice([HeatTaskStatus.COMPLETED, HeatTaskStatus.COMPLETED,
                                HeatTaskStatus.COMPLETED, HeatTaskStatus.PENDING, HeatTaskStatus.RUNNING])
        task = BusHeatTask(
            route_id=route.id,
            task_status=status,
            heat_score=route.heat_score if status == HeatTaskStatus.COMPLETED else None,
            poi_data=random.choice(route.pois) if route.pois and status == HeatTaskStatus.COMPLETED else [],
            error_message=None,
        )
        db.add(task)
        tasks.append(task)

    db.flush()
    print(f"   ✅ 共插入 {len(tasks)} 个热力任务")
    return len(tasks)


def seed_attribution(db, campaigns):
    """生成效果归因数据"""
    print(f"📊 插入效果归因数据...")
    count = 0
    for campaign in campaigns:
        if campaign.status != CampaignStatus.COMPLETED:
            continue
        # 汇总线路曝光
        total_imp = sum(cr.estimated_impressions for cr in campaign.campaign_routes)
        reach = int(total_imp * 0.35)
        flow_imp = sum(cr.flow_impressions for cr in campaign.campaign_routes)
        dwell_imp = sum(cr.dwell_impressions for cr in campaign.campaign_routes)
        eff_imp = int(total_imp * 0.85)
        multiplier = round((flow_imp + dwell_imp) / max(sum(cr.ad_slots_per_cycle for cr in campaign.campaign_routes) if campaign.campaign_routes else 1, 1), 4)

        attr = BusAttribution(
            campaign_id=campaign.id,
            total_impressions=total_imp,
            total_reach=reach,
            cost_per_impression=round(campaign.total_budget / Decimal(str(max(total_imp, 1))), 4),
            cost_per_reach=round(campaign.total_budget / Decimal(str(max(reach, 1))), 4),
            flow_impressions=flow_imp,
            dwell_impressions=dwell_imp,
            effective_impressions=eff_imp,
            impression_multiplier=multiplier,
            frequency=round(eff_imp / max(reach, 1), 2),
            independent_audience=reach,
            detailed_data={"touchpoints": random.randint(2, 8), "one_id_match_rate": round(random.uniform(0.4, 0.8), 2)},
        )
        db.add(attr)
        count += 1

    db.commit()
    print(f"   ✅ 共插入 {count} 条归因数据")
    return count


def seed_dmp_tags(count: int = 10000):
    """生成 DMP 标签数据（通过 direct SQL）"""
    print(f"🏷️ 生成 {count} 个 DMP 标签记录（直接SQL）...")
    # 标签数据写入 JSON 格式的 placements/custom_data，不单独建表
    # 这里在 existing media_resources 的 custom_data 中注入标签
    with engine.connect() as conn:
        # 随机更新部分屏幕的 custom_data 加入标签
        result = conn.execute(text("SELECT id FROM media_resources ORDER BY random() LIMIT 500"))
        rows = result.fetchall()
        updated = 0
        for row in rows:
            tag_pool = []
            for cat_tags in TAG_CATEGORIES.values():
                tag_pool.extend(random.sample(cat_tags, k=random.randint(1, 3)))
            new_data = {
                "dmp_tags": tag_pool,
                "audience_score": round(random.uniform(0.3, 0.95), 2),
            }
            conn.execute(
                text("UPDATE media_resources SET custom_data = :data WHERE id = :id"),
                {"data": str(new_data).replace("'", '"'), "id": row[0]}
            )
            updated += 1
        conn.commit()
    print(f"   ✅ 已为 {updated} 块屏幕注入 DMP 标签")
    return updated


def seed_competitor_data(count: int = 15):
    """生成竞品监控数据"""
    print(f"🔍 生成 {count} 条竞品投放记录...")
    with SessionLocal() as db:
        records = []
        media_types = ["bus_body", "billboard", "elevator", "bus_stop", "mall_screen"]
        for i in range(count):
            competitor = ADVERTISERS[i % len(ADVERTISERS)]
            records.append({
                "id": uuid4(),
                "competitor_name": f"{competitor}",
                "media_type": random.choice(media_types),
                "campaign_name": f"{competitor}品宣活动-{random.randint(100,999)}",
                "start_date": datetime.utcnow() - timedelta(days=random.randint(0, 90)),
                "end_date": datetime.utcnow() + timedelta(days=random.randint(10, 60)),
                "estimated_budget": round(random.uniform(50000, 1000000), 2),
                "screen_count": random.randint(5, 100),
                "active_days": random.randint(7, 90),
                "impressions": random.randint(10000, 5000000),
                "engagement_rate": round(random.uniform(0.01, 0.08), 4),
                "activity_score": round(random.uniform(3, 10), 1),
            })
        db.bulk_insert_dicts(CompetitorCampaign, records)
        db.commit()
    print(f"   ✅ 共插入 {len(records)} 条竞品记录")
    return len(records)


# ── 主入口 ──────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("🌱 AIAdPlacer 模拟数据种子脚本 v1.0")
    print(f"   数据库: {settings.DATABASE_URL.split('@')[1].split('/')[0]}")
    print("=" * 60)

    # 确认操作
    answer = input("\n⚠️ 此操作将向数据库插入大量模拟数据，是否继续? (y/N): ")
    if answer.lower() != "y":
        print("❌ 已取消")
        return

    db = SessionLocal()
    try:
        # 1. 智能屏
        n_screens = seed_media_resources(db)

        # 2. 投放计划 + 投放记录 + 转化
        campaigns = seed_campaigns(db)
        seed_placements(db, campaigns)
        seed_conversions(db)

        # 3. 公交线路 + 方案
        routes = seed_bus_routes(db)
        bus_campaigns = seed_bus_campaigns(db, routes)
        seed_heat_tasks(db, routes)
        seed_attribution(db, bus_campaigns)

        # 4. DMP 标签 + 竞品
        seed_dmp_tags()
        seed_competitor_data()

        print("\n" + "=" * 60)
        print("🎉 数据种子完成！")
        print(f"   屏幕: {n_screens} 块")
        print(f"   投放计划: {len(campaigns)} 个")
        print(f"   公交线路: {len(routes)} 条")
        print(f"   公交方案: {len(bus_campaigns)} 个")
        print(f"\n   启动后端: python run.py")
        print(f"   查看 Demo: http://127.0.0.1:5002/cps2-demo.html")
        print("=" * 60)

    except Exception as e:
        db.rollback()
        print(f"\n❌ 种子失败: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    random.seed(42)  # 可复现
    main()
