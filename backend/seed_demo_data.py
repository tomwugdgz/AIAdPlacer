"""
演示数据填充脚本
运行: python seed_demo_data.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.models import SessionLocal, MediaResource, Campaign, Placement, Conversion
from datetime import date, datetime, timedelta
from decimal import Decimal
import uuid
import random

def seed_data():
    db = SessionLocal()
    try:
        print("🌱 开始填充演示数据...")
        
        # 清理现有数据
        db.query(Conversion).delete()
        db.query(Placement).delete()
        db.query(Campaign).delete()
        db.query(MediaResource).delete()
        db.commit()
        print("✅ 清理完成")
        
        # ========== 创建媒体资源 ==========
        media_resources = [
            {
                "name": "天河城电梯广告 #A102",
                "type": "offline",
                "category": "elevator",
                "latitude": 23.136,
                "longitude": 113.326,
                "address": "广州市天河区体育东路天河城",
                "coverage_radius": 500,
                "daily_price": 800,
                "daily_impressions": 5000,
                "status": "booked",
                "custom_data": {"building": "天河城", "floor": "B1-5F"},
            },
            {
                "name": "北京路户外大屏 #B045",
                "type": "offline",
                "category": "billboard",
                "latitude": 23.125,
                "longitude": 113.264,
                "address": "广州市越秀区北京路步行街",
                "coverage_radius": 1000,
                "daily_price": 2500,
                "daily_impressions": 15000,
                "status": "available",
                "custom_data": {"size": "12m×8m", "resolution": "4K"},
            },
            {
                "name": "微信朋友圈广告-广州",
                "type": "online",
                "category": "social",
                "latitude": 23.132,
                "longitude": 113.267,
                "address": "广州市全域",
                "coverage_radius": 50000,
                "daily_price": 5000,
                "daily_impressions": 100000,
                "status": "booked",
                "custom_data": {"platform": "WeChat", "format": "video"},
            },
            {
                "name": "珠江新城公交站牌 #C078",
                "type": "offline",
                "category": "bus_stop",
                "latitude": 23.118,
                "longitude": 113.321,
                "address": "广州市天河区珠江新城花城大道",
                "coverage_radius": 300,
                "daily_price": 400,
                "daily_impressions": 3000,
                "status": "booked",
                "custom_data": {"line": "B1, 40, 197"},
            },
            {
                "name": "抖音信息流广告-广州",
                "type": "online",
                "category": "app",
                "latitude": 23.130,
                "longitude": 113.265,
                "address": "广州市全域",
                "coverage_radius": 50000,
                "daily_price": 3500,
                "daily_impressions": 80000,
                "status": "available",
                "custom_data": {"platform": "Douyin", "format": "feed"},
            },
            {
                "name": "海珠区江南西电梯广告",
                "type": "offline",
                "category": "elevator",
                "latitude": 23.099,
                "longitude": 113.264,
                "address": "广州市海珠区江南西路",
                "coverage_radius": 400,
                "daily_price": 600,
                "daily_impressions": 4000,
                "status": "booked",
                "custom_data": {"building": "江南新地"},
            },
            {
                "name": "番禺区万达户外广告",
                "type": "offline",
                "category": "billboard",
                "latitude": 22.948,
                "longitude": 113.366,
                "address": "广州市番禺区万达广场",
                "coverage_radius": 800,
                "daily_price": 1500,
                "daily_impressions": 10000,
                "status": "booked",
                "custom_data": {"size": "8m×5m"},
            },
            {
                "name": "白云区白云大道公交站",
                "type": "offline",
                "category": "bus_stop",
                "latitude": 23.185,
                "longitude": 113.259,
                "address": "广州市白云区白云大道",
                "coverage_radius": 250,
                "daily_price": 300,
                "daily_impressions": 2000,
                "status": "booked",
                "custom_data": {"line": "76, 804"},
            },
        ]
        
        media_ids = []
        for m in media_resources:
            media = MediaResource(**m)
            db.add(media)
            db.commit()
            db.refresh(media)
            media_ids.append(media.id)
        
        print(f"✅ 创建 {len(media_resources)} 个媒体资源")
        
        # ========== 创建投放计划 ==========
        campaigns = [
            {
                "name": "2026春季新品推广",
                "description": "春季新品全渠道投放计划，覆盖广州主要商圈",
                "budget": 150000,
                "start_date": date(2026, 3, 1),
                "end_date": date(2026, 4, 30),
                "target_audience": {"age": "18-35", "gender": "all", "interests": ["shopping", "fashion"]},
                "status": "active",
                "ai_recommendations": ["重点投放天河区和越秀区", "早晚高峰加强电梯广告"],
            },
            {
                "name": "品牌认知度提升计划",
                "description": "提升品牌在二三线商圈的认知度",
                "budget": 80000,
                "start_date": date(2026, 4, 1),
                "end_date": date(2026, 5, 31),
                "target_audience": {"age": "25-45", "gender": "all", "interests": ["lifestyle"]},
                "status": "active",
                "ai_recommendations": ["增加番禺区和白云区投放"],
            },
        ]
        
        campaign_ids = []
        for c in campaigns:
            campaign = Campaign(**c)
            db.add(campaign)
            db.commit()
            db.refresh(campaign)
            campaign_ids.append(campaign.id)
        
        print(f"✅ 创建 {len(campaigns)} 个投放计划")
        
        # ========== 创建投放记录（过去30天） ==========
        placements = []
        start_date = date(2026, 3, 15)
        
        for i in range(50):
            media = db.query(MediaResource).filter(MediaResource.status == "booked").all()
            if not media:
                continue
            
            m = random.choice(media)
            d = start_date + timedelta(days=random.randint(0, 45))
            
            # 根据媒体类型生成不同的效果数据
            if m.category in ["elevator", "billboard"]:
                impressions = m.daily_impressions + random.randint(-500, 500)
                ctr = random.uniform(0.02, 0.06)
            else:
                impressions = m.daily_impressions + random.randint(-1000, 1000)
                ctr = random.uniform(0.03, 0.08)
            
            clicks = int(impressions * ctr)
            cvr = random.uniform(0.02, 0.06)
            conversions = int(clicks * cvr)
            cost = float(m.daily_price or 500)
            
            placement = Placement(
                campaign_id=random.choice(campaign_ids),
                media_id=m.id,
                date=d,
                impressions=max(0, impressions),
                clicks=max(0, clicks),
                conversions=max(0, conversions),
                cost=cost,
                latitude=m.latitude,
                longitude=m.longitude,
                extra_data={"day_of_week": d.weekday()},
            )
            db.add(placement)
            placements.append(placement)
        
        db.commit()
        print(f"✅ 创建 {len(placements)} 条投放记录")
        
        # ========== 创建转化数据 ==========
        conversions = []
        for p in placements[:30]:  # 取前30条投放记录
            if p.conversions > 0:
                for j in range(min(p.conversions, 5)):  # 每条最多5个转化
                    conversion = Conversion(
                        placement_id=p.id,
                        user_id=f"user_{random.randint(1000, 9999)}",
                        conversion_type=random.choice(["purchase", "signup", "download"]),
                        conversion_value=Decimal(f"{random.uniform(50, 500):.2f}"),
                        touchpoint_order=random.randint(1, 3),
                        attribution_model=random.choice(["first", "last", "linear", "time_decay"]),
                        location_lat=p.latitude + random.uniform(-0.01, 0.01),
                        location_lng=p.longitude + random.uniform(-0.01, 0.01),
                    )
                    db.add(conversion)
                    conversions.append(conversion)
        
        db.commit()
        print(f"✅ 创建 {len(conversions)} 条转化数据")
        
        print("\n🎉 演示数据填充完成！")
        print(f"\n数据概览:")
        print(f"  - 媒体资源: {len(media_resources)} 个")
        print(f"  - 投放计划: {len(campaigns)} 个")
        print(f"  - 投放记录: {len(placements)} 条")
        print(f"  - 转化数据: {len(conversions)} 条")
        
    except Exception as e:
        db.rollback()
        print(f"❌ 填充数据失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
