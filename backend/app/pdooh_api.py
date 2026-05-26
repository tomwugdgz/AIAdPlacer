"""
pDOOH 后端 API - 连接真实 pdooh 数据库
提供智能屏、人锚点、POI、投放计划的 REST API
"""
import psycopg2
import psycopg2.extras
import json
import math
from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List
from pydantic import BaseModel

router = APIRouter(prefix="/api/v2/pdooh")

# ── 数据库连接 ────────────────────────────────────────────────────────
def get_pdooh_conn():
    return psycopg2.connect(
        host="127.0.0.1",
        port=5432,
        database="pdooh",
        user="quantdinger",
        password="quantdinger123",
        cursor_factory=psycopg2.extras.RealDictCursor
    )

# ── Pydantic 模型 ────────────────────────────────────────────────────
class CampaignCreate(BaseModel):
    name: str
    advertiser: str
    target_tags: dict
    screen_ids: List[str]
    start_date: str
    end_date: str
    budget: float
    creative_type: str = "image"
    ai_generated: bool = False

# ── 工具函数 ──────────────────────────────────────────────────────────
def haversine(lat1, lng1, lat2, lng2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lng2 - lng1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlam/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

def row_to_dict(row):
    if row is None:
        return None
    d = dict(row)
    for k, v in d.items():
        if hasattr(v, 'isoformat'):
            d[k] = v.isoformat()
        elif hasattr(v, '__float__'):
            d[k] = float(v)
    return d

# ════════════════════════════════════════════════════════════════
# 1. 智能屏 API
# ════════════════════════════════════════════════════════════════

@router.get("/screens")
def list_screens(
    lat: Optional[float] = Query(None, description="纬度（用于距离排序）"),
    lng: Optional[float] = Query(None, description="经度（用于距离排序）"),
    radius: Optional[float] = Query(None, description="半径（米），需配合 lat/lng"),
    district: Optional[str] = Query(None, description="行政区划筛选"),
    screen_type: Optional[str] = Query(None, description="屏类型：unit_door/elevator/community_gate"),
    min_traffic: Optional[int] = Query(None, description="最小日均人流"),
    limit: int = Query(200, le=2000),
    offset: int = Query(0),
):
    conn = get_pdooh_conn()
    try:
        where = ["1=1"]
        params = []
        if lat is not None and lng is not None and radius is not None:
            lat_delta = radius / 111000.0
            lng_delta = radius / (111000.0 * math.cos(math.radians(lat)))
            where.append("latitude BETWEEN %s AND %s")
            params.extend([lat - lat_delta, lat + lat_delta])
            where.append("longitude BETWEEN %s AND %s")
            params.extend([lng - lng_delta, lng + lng_delta])
        if district:
            where.append("district = %s")
            params.append(district)
        if screen_type:
            where.append("screen_type = %s")
            params.append(screen_type)
        if min_traffic:
            where.append("daily_traffic >= %s")
            params.append(min_traffic)

        sql = f"""
            SELECT id, external_id, name, address, district,
                   latitude AS lat, longitude AS lng,
                   screen_type, size_width, size_height, orientation,
                   daily_traffic, audience_tags, status, install_date
            FROM screen
            WHERE {' AND '.join(where)}
            ORDER BY id
            LIMIT %s OFFSET %s
        """
        params.extend([limit, offset])
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()

        result = [row_to_dict(r) for r in rows]

        if lat is not None and lng is not None:
            for r in result:
                r["distance_m"] = round(haversine(lat, lng, r["lat"], r["lng"]), 1)
            if radius is not None:
                result = [r for r in result if r["distance_m"] <= radius]
            result.sort(key=lambda x: x.get("distance_m", 999999))

        count_sql = f"SELECT COUNT(*) FROM screen WHERE {' AND '.join(where)}"
        with conn.cursor() as cur:
            cur.execute(count_sql, params[:-2])
            total = cur.fetchone()["count"]

        return {"total": total, "limit": limit, "offset": offset, "data": result}
    finally:
        conn.close()


@router.get("/screens/{external_id}")
def get_screen(external_id: str):
    conn = get_pdooh_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, external_id, name, address, district,
                       latitude AS lat, longitude AS lng,
                       screen_type, size_width, size_height, orientation,
                       daily_traffic, audience_tags, status, install_date
                FROM screen WHERE external_id = %s
            """, (external_id,))
            row = cur.fetchone()
        if not row:
            raise HTTPException(404, "Screen not found")
        return row_to_dict(row)
    finally:
        conn.close()


@router.get("/screens/{external_id}/audience")
def get_screen_audience(external_id: str):
    conn = get_pdooh_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM screen WHERE external_id = %s", (external_id,))
            scr = cur.fetchone()
        if not scr:
            raise HTTPException(404, "Screen not found")
        screen_id = scr["id"]

        with conn.cursor() as cur:
            cur.execute("""
                SELECT person_taid, age, gender, life_stage,
                       tag_category, tag_value, confidence,
                       days_since_seen
                FROM vw_screen_audience
                WHERE screen_id = %s
                LIMIT 500
            """, (screen_id,))
            rows = cur.fetchall()

        if not rows:
            return {"screen_id": screen_id, "external_id": external_id,
                    "total_persons": 0, "age_dist": {}, "gender_dist": {},
                    "interest_top10": [], "persons": []}

        import collections
        age_dist = {}
        gender_dist = {}
        interest_counter = {}
        persons = []
        for r in rows:
            d = row_to_dict(r)
            persons.append(d)
            a = d.get("age") or "unknown"
            age_dist[a] = age_dist.get(a, 0) + 1
            g = d.get("gender") or "unknown"
            gender_dist[g] = gender_dist.get(g, 0) + 1
            cat = d.get("tag_category")
            if cat:
                interest_counter[cat] = interest_counter.get(cat, 0) + 1

        interest_top10 = collections.Counter(interest_counter).most_common(10)

        return {
            "screen_id": screen_id,
            "external_id": external_id,
            "total_persons": len(persons),
            "age_dist": age_dist,
            "gender_dist": gender_dist,
            "interest_top10": [{"category": k, "count": v} for k, v in interest_top10],
            "persons": persons[:50]
        }
    except Exception as e:
        raise HTTPException(500, str(e))
    finally:
        conn.close()

# ════════════════════════════════════════════════════════════════
# 2. 人锚点 API
# ════════════════════════════════════════════════════════════════

@router.get("/persons")
def list_persons(
    tag_category: Optional[str] = Query(None),
    tag_value: Optional[str] = Query(None),
    gender: Optional[str] = Query(None),
    min_age: Optional[int] = Query(None),
    max_age: Optional[int] = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0),
):
    conn = get_pdooh_conn()
    try:
        base_sql = """
            SELECT DISTINCT pa.taid, pa.age, pa.gender, pa.life_stage,
                   pa.home_lat, pa.home_lng
            FROM person_anchor pa
        """
        where_clauses = []
        params = []
        if tag_category or tag_value:
            base_sql += " LEFT JOIN person_dmp_tags pdt ON pa.taid = pdt.person_taid"
            if tag_category:
                where_clauses.append("pdt.tag_category = %s")
                params.append(tag_category)
            if tag_value:
                where_clauses.append("pdt.tag_value = %s")
                params.append(tag_value)
        if gender:
            where_clauses.append("pa.gender = %s")
            params.append(gender)
        if min_age:
            where_clauses.append("pa.age >= %s")
            params.append(min_age)
        if max_age:
            where_clauses.append("pa.age <= %s")
            params.append(max_age)
        if where_clauses:
            base_sql += " WHERE " + " AND ".join(where_clauses)
        base_sql += " ORDER BY pa.taid LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        with conn.cursor() as cur:
            cur.execute(base_sql, params)
            rows = cur.fetchall()
        return {"total": len(rows), "data": [row_to_dict(r) for r in rows]}
    finally:
        conn.close()


@router.get("/persons/{taid}/tags")
def get_person_tags(taid: str):
    conn = get_pdooh_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT tag_category, tag_value, confidence, source,
                       last_updated, expires_at
                FROM person_dmp_tags
                WHERE person_taid = %s
                ORDER BY last_updated DESC
            """, (taid,))
            rows = cur.fetchall()
        return {"taid": taid, "total_tags": len(rows),
                "tags": [row_to_dict(r) for r in rows]}
    finally:
        conn.close()


@router.get("/persons/{taid}/trajectory")
def get_person_trajectory(
    taid: str,
    days: int = Query(7, description="查询最近N天轨迹"),
):
    conn = get_pdooh_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT st.id, st.person_taid, st.trajectory_date,
                       st.location_type, st.location_name,
                       st.latitude AS lat, st.longitude AS lng,
                       st.screen_external_id, st.confidence
                FROM spatial_trajectory st
                WHERE st.person_taid = %s
                  AND st.trajectory_date >= CURRENT_DATE - INTERVAL '%s days'
                ORDER BY st.trajectory_date DESC
            """, (taid, days))
            rows = cur.fetchall()
        return {"taid": taid, "days": days,
                "total_records": len(rows),
                "trajectory": [row_to_dict(r) for r in rows]}
    finally:
        conn.close()

# ════════════════════════════════════════════════════════════════
# 3. POI API
# ════════════════════════════════════════════════════════════════

@router.get("/poi")
def list_poi(
    lat: Optional[float] = Query(None),
    lng: Optional[float] = Query(None),
    radius: Optional[float] = Query(None, description="半径（米）"),
    category: Optional[str] = Query(None, description="POI类别"),
    name_keyword: Optional[str] = Query(None),
    limit: int = Query(200, le=1000),
):
    conn = get_pdooh_conn()
    try:
        where = ["1=1"]
        params = []
        if lat is not None and lng is not None and radius is not None:
            lat_d = radius / 111000.0
            lng_d = radius / (111000.0 * math.cos(math.radians(lat)))
            where.append("poi_lat BETWEEN %s AND %s")
            params.extend([lat - lat_d, lat + lat_d])
            where.append("poi_lng BETWEEN %s AND %s")
            params.extend([lng - lng_d, lng + lng_d])
        if category:
            where.append("poi_category = %s")
            params.append(category)
        if name_keyword:
            where.append("poi_name ILIKE %s")
            params.append(f"%{name_keyword}%")

        sql = f"""
            SELECT id, poi_id, poi_name, poi_category, poi_sub_category,
                   poi_lat AS lat, poi_lng AS lng,
                   address, district, screen_external_id
            FROM poi_data
            WHERE {' AND '.join(where)}
            ORDER BY poi_id
            LIMIT %s
        """
        params.append(limit)
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()

        result = [row_to_dict(r) for r in rows]

        if lat is not None and lng is not None:
            for r in result:
                r["distance_m"] = round(haversine(lat, lng, r["lat"], r["lng"]), 1)
            if radius is not None:
                result = [r for r in result if r["distance_m"] <= radius]
            result.sort(key=lambda x: x.get("distance_m", 999999))

        return {"total": len(result), "data": result}
    finally:
        conn.close()

# ════════════════════════════════════════════════════════════════
# 4. 投放计划 API
# ════════════════════════════════════════════════════════════════

@router.post("/campaigns")
def create_campaign(camp: CampaignCreate):
    conn = get_pdooh_conn()
    try:
        with conn.cursor() as cur:
            # 确保序列存在
            cur.execute("CREATE SEQUENCE IF NOT EXISTS ai_campaign_seq START WITH 1;")
            conn.commit()
            # 确保表存在
            cur.execute("""
                CREATE TABLE IF NOT EXISTS ai_campaign (
                    id SERIAL PRIMARY KEY,
                    campaign_id VARCHAR(64) UNIQUE NOT NULL DEFAULT 'CMP' || to_char(NOW(), 'YYYYMMDD') || '_' || nextval('ai_campaign_seq'),
                    name VARCHAR(200) NOT NULL,
                    advertiser VARCHAR(100),
                    target_tags JSONB,
                    screen_ids JSONB,
                    start_date DATE,
                    end_date DATE,
                    budget NUMERIC(12,2),
                    creative_type VARCHAR(50),
                    ai_generated BOOLEAN DEFAULT FALSE,
                    status VARCHAR(20) DEFAULT 'draft',
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                );
            """)
            conn.commit()
            cur.execute("""
                INSERT INTO ai_campaign
                    (name, advertiser, target_tags, screen_ids,
                     start_date, end_date, budget, creative_type, ai_generated)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, campaign_id, name, status, created_at
            """, (
                camp.name, camp.advertiser,
                json.dumps(camp.target_tags, ensure_ascii=False),
                json.dumps(camp.screen_ids, ensure_ascii=False),
                camp.start_date, camp.end_date,
                camp.budget, camp.creative_type, camp.ai_generated
            ))
            row = cur.fetchone()
            conn.commit()
        return {"success": True, "campaign": row_to_dict(row)}
    except Exception as e:
        conn.rollback()
        raise HTTPException(500, str(e))
    finally:
        conn.close()


@router.get("/campaigns")
def list_campaigns(
    status: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
):
    conn = get_pdooh_conn()
    try:
        where = []
        params = []
        if status:
            where.append("status = %s")
            params.append(status)
        sql = """
            SELECT id, campaign_id, name, advertiser, status,
                   start_date, end_date, budget, creative_type,
                   ai_generated, created_at
            FROM ai_campaign
        """
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY created_at DESC LIMIT %s"
        params.append(limit)
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
        return {"total": len(rows), "data": [row_to_dict(r) for r in rows]}
    finally:
        conn.close()


@router.get("/stats/districts")
def get_district_stats():
    conn = get_pdooh_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT district, COUNT(*) AS screen_count,
                       SUM(daily_traffic) AS total_daily_traffic,
                       AVG(daily_traffic) AS avg_daily_traffic
                FROM screen
                WHERE district IS NOT NULL
                GROUP BY district
                ORDER BY screen_count DESC
            """)
            rows = cur.fetchall()
        return {"data": [row_to_dict(r) for r in rows]}
    finally:
        conn.close()
