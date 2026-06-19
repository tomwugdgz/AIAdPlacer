"""
数据库 RESTful API 接口测试用例

测试 db_api.py 的所有 API 端点

作者: 寇豆码（Kou）
日期: 2026-03-04
"""

import pytest
import json
from pathlib import Path
from app import create_app
from app.db_dao import DB_PATH as original_db_path, get_db_connection


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def app():
    """创建测试应用"""
    app = create_app({"TESTING": True})
    return app


@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()


@pytest.fixture
def setup_test_db(tmp_path):
    """
    创建测试数据库并替换原始数据库路径
    
    Args:
        tmp_path: pytest 临时路径 fixture
        
    Yields:
        临时数据库路径
    """
    import sqlite3
    from app import db_dao as db_dao_module
    
    # 创建临时数据库
    test_db_path = tmp_path / "test_qinlin.db"
    conn = sqlite3.connect(str(test_db_path))
    conn.execute("PRAGMA journal_mode=WAL")
    
    # 创建测试表
    conn.execute("""
        CREATE TABLE "单元门点位" (
            id INTEGER PRIMARY KEY,
            省份 TEXT,
            城市 TEXT,
            区域 TEXT,
            商圈 TEXT,
            楼盘类型 TEXT,
            楼栋数量 INTEGER,
            单元门数量 INTEGER,
            楼盘价格 REAL,
            住户数量 INTEGER,
            经度 REAL,
            纬度 REAL
        )
    """)
    
    conn.execute("""
        CREATE TABLE "客户通讯录" (
            id INTEGER PRIMARY KEY,
            客户简称 TEXT,
            品牌名称 TEXT,
            决策城市 TEXT,
            行业 TEXT,
            联系人 TEXT,
            手机 TEXT
        )
    """)
    
    # 插入测试数据
    test_data = [
        (1, "广东省", "广州市", "天河区", "珠江新城", "住宅", 10, 20, 50000, 500, 113.3, 23.1),
        (2, "广东省", "广州市", "越秀区", "北京路", "住宅", 8, 16, 45000, 400, 113.2, 23.2),
        (3, "广东省", "深圳市", "南山区", "科技园", "商业", 15, 30, 80000, 800, 114.0, 22.5),
        (4, "湖南省", "长沙市", "岳麓区", "梅溪湖", "住宅", 12, 24, 35000, 600, 112.9, 28.2),
        (5, "广东省", "广州市", "天河区", "天河路", "商业", 20, 40, 55000, 1000, None, None),  # 无经纬度
    ]
    
    conn.executemany(
        'INSERT INTO "单元门点位" VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
        test_data
    )
    
    client_data = [
        (1, "华为技术", "华为", "深圳市", "通信", "张三", "13800138000"),
        (2, "腾讯科技", "腾讯", "深圳市", "互联网", "李四", "13800138001"),
        (3, "阿里巴巴", "阿里", "杭州市", "互联网", "王五", "13800138002"),
    ]
    
    conn.executemany(
        'INSERT INTO "客户通讯录" VALUES (?, ?, ?, ?, ?, ?, ?)',
        client_data
    )
    
    conn.commit()
    conn.close()
    
    # 替换原始数据库路径
    original_path = db_dao_module.DB_PATH
    db_dao_module.DB_PATH = test_db_path
    
    yield test_db_path
    
    # 恢复原始路径
    db_dao_module.DB_PATH = original_path


# ── 测试用例 ─────────────────────────────────────────────────────────────────────

class TestGetTables:
    """测试 GET /api/v2/db/tables"""
    
    def test_success(self, client, setup_test_db):
        """测试成功获取所有表"""
        response = client.get("/api/v2/db/tables")
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert len(data["data"]) == 2
        assert data["total_tables"] == 2
        
        # 验证表信息
        table_names = [t["name"] for t in data["data"]]
        assert "单元门点位" in table_names
        assert "客户通讯录" in table_names
    
    def test_database_not_found(self, client, monkeypatch):
        """测试数据库文件不存在时返回 404"""
        from app import db_dao as db_dao_module
        original_path = db_dao_module.DB_PATH
        db_dao_module.DB_PATH = Path("/nonexistent/db.db")
        
        response = client.get("/api/v2/db/tables")
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data["success"] is False
        assert data["code"] == "DATABASE_NOT_FOUND"
        
        db_dao_module.DB_PATH = original_path


class TestQueryTableData:
    """测试 GET /api/v2/db/<table_name>"""
    
    def test_success(self, client, setup_test_db):
        """测试成功查询表数据"""
        response = client.get("/api/v2/db/单元门点位?page=1&page_size=3")
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert len(data["data"]) == 3
        assert data["pagination"]["total"] == 5
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["page_size"] == 3
        assert data["pagination"]["total_pages"] == 2
    
    def test_filter_by_city(self, client, setup_test_db):
        """测试按城市筛选"""
        response = client.get("/api/v2/db/单元门点位?city=广州")
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["pagination"]["total"] == 3  # 3 条广州记录
        assert all(row["城市"] == "广州市" for row in data["data"])
    
    def test_filter_by_province(self, client, setup_test_db):
        """测试按省份筛选"""
        response = client.get("/api/v2/db/单元门点位?province=广东")
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["pagination"]["total"] == 4  # 4 条广东记录
    
    def test_filter_by_district(self, client, setup_test_db):
        """测试按区域筛选"""
        response = client.get("/api/v2/db/单元门点位?district=天河")
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["pagination"]["total"] == 2  # 2 条天河区记录
    
    def test_filter_by_business_district(self, client, setup_test_db):
        """测试按商圈筛选"""
        response = client.get("/api/v2/db/单元门点位?business_district=珠江")
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["pagination"]["total"] == 1
    
    def test_filter_by_price_range(self, client, setup_test_db):
        """测试按价格范围筛选"""
        response = client.get("/api/v2/db/单元门点位?min_price=50000&max_price=60000")
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["pagination"]["total"] == 3  # 3 条价格在 50000-60000 之间
    
    def test_pagination(self, client, setup_test_db):
        """测试分页功能"""
        # 第 1 页
        response1 = client.get("/api/v2/db/单元门点位?page=1&page_size=2")
        data1 = json.loads(response1.data)
        assert len(data1["data"]) == 2
        assert data1["pagination"]["page"] == 1
        
        # 第 2 页
        response2 = client.get("/api/v2/db/单元门点位?page=2&page_size=2")
        data2 = json.loads(response2.data)
        assert len(data2["data"]) == 2
        assert data2["pagination"]["page"] == 2
        
        # 确保两页数据不重复
        ids1 = [row["id"] for row in data1["data"]]
        ids2 = [row["id"] for row in data2["data"]]
        assert set(ids1).isdisjoint(set(ids2))
    
    def test_invalid_page(self, client, setup_test_db):
        """测试无效的页码"""
        response = client.get("/api/v2/db/单元门点位?page=0")
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["success"] is False
        assert data["code"] == "INVALID_PARAM"
    
    def test_invalid_page_size(self, client, setup_test_db):
        """测试无效的每页记录数"""
        response = client.get("/api/v2/db/单元门点位?page_size=0")
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["success"] is False
        assert data["code"] == "INVALID_PARAM"
        
        # 超过最大限制
        response2 = client.get("/api/v2/db/单元门点位?page_size=1001")
        assert response2.status_code == 400
    
    def test_invalid_price(self, client, setup_test_db):
        """测试无效的价格参数"""
        response = client.get("/api/v2/db/单元门点位?min_price=abc")
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["success"] is False
        assert data["code"] == "INVALID_PARAM"
    
    def test_table_not_found(self, client, setup_test_db):
        """测试表名不存在"""
        response = client.get("/api/v2/db/不存在的表")
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["success"] is False


class TestGetStats:
    """测试 GET /api/v2/db/stats/<table_name>"""
    
    def test_success(self, client, setup_test_db):
        """测试成功获取统计信息"""
        response = client.get("/api/v2/db/stats/单元门点位")
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert "data" in data
        
        stats = data["data"]
        assert stats["total_count"] == 5
        assert "city_stats" in stats
        assert stats["city_stats"]["广州市"] == 3
        assert stats["city_stats"]["深圳市"] == 1
        assert stats["city_stats"]["长沙市"] == 1
        assert stats["has_coordinates"] == 4
        assert stats["null_coordinates"] == 1
    
    def test_table_not_found(self, client, setup_test_db):
        """测试表名不存在"""
        response = client.get("/api/v2/db/stats/不存在的表")
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["success"] is False
        assert data["code"] == "TABLE_NOT_FOUND"


class TestSearchData:
    """测试 GET /api/v2/db/search/<table_name>"""
    
    def test_success(self, client, setup_test_db):
        """测试成功搜索"""
        response = client.get("/api/v2/db/search/单元门点位?q=广州")
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["total"] == 3  # 3 条包含"广州"的记录
        assert all("广州" in str(row) for row in data["data"])
    
    def test_no_results(self, client, setup_test_db):
        """测试搜索无结果"""
        response = client.get("/api/v2/db/search/单元门点位?q=北京")
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["total"] == 0
        assert len(data["data"]) == 0
    
    def test_missing_keyword(self, client, setup_test_db):
        """测试缺少搜索关键词"""
        response = client.get("/api/v2/db/search/单元门点位")
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["success"] is False
        assert data["code"] == "MISSING_PARAM"
    
    def test_empty_keyword(self, client, setup_test_db):
        """测试空关键词"""
        response = client.get("/api/v2/db/search/单元门点位?q=")
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["success"] is False


class TestSearchClients:
    """测试 GET /api/v2/db/clients/search"""
    
    def test_search_by_keyword(self, client, setup_test_db):
        """测试按关键词搜索"""
        response = client.get("/api/v2/db/clients/search?keyword=华为")
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["total"] == 1
        assert data["data"][0]["客户简称"] == "华为技术"
    
    def test_search_by_city(self, client, setup_test_db):
        """测试按城市筛选"""
        response = client.get("/api/v2/db/clients/search?city=深圳")
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["total"] == 2  # 2 条深圳记录
        assert all(row["决策城市"] == "深圳市" for row in data["data"])
    
    def test_search_by_industry(self, client, setup_test_db):
        """测试按行业筛选"""
        response = client.get("/api/v2/db/clients/search?industry=互联网")
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["total"] == 2  # 2 条互联网记录
    
    def test_search_with_limit(self, client, setup_test_db):
        """测试限制返回数量"""
        response = client.get("/api/v2/db/clients/search?limit=2")
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert len(data["data"]) <= 2
    
    def test_search_no_filters(self, client, setup_test_db):
        """测试不带任何筛选条件"""
        response = client.get("/api/v2/db/clients/search")
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["total"] == 3  # 返回所有 3 条记录


class TestGetPoints:
    """测试 GET /api/v2/db/points/<point_type>"""
    
    def test_unit_door(self, client, setup_test_db, monkeypatch):
        """测试获取单元门点位"""
        # Mock get_points_by_type 函数
        from app import db_dao as db_dao_module
        original_func = db_dao_module.get_points_by_type
        
        # 由于测试数据库中表名是"单元门点位"，而 point_type="unit_door" 会映射到"单元门点位"
        # 所以这里应该能正常工作
        response = client.get("/api/v2/db/points/unit_door?city=广州&limit=50")
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["total"] == 3  # 3 条广州记录
        assert data["filters"]["point_type"] == "unit_door"
        assert data["filters"]["city"] == "广州"
    
    def test_invalid_point_type(self, client, setup_test_db):
        """测试无效的点位类型"""
        response = client.get("/api/v2/db/points/invalid_type")
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["success"] is False


class TestApiDocs:
    """测试 GET /api/v2/db/docs"""
    
    def test_success(self, client):
        """测试成功获取 API 文档"""
        response = client.get("/api/v2/db/docs")
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "name" in data
        assert "version" in data
        assert "endpoints" in data
        assert len(data["endpoints"]) > 0


# ── 集成测试 ─────────────────────────────────────────────────────────────────────

class TestIntegration:
    """集成测试：测试多个 API 的组合使用"""
    
    def test_query_then_stats(self, client, setup_test_db):
        """测试先查询再统计的流程"""
        # 1. 查询广州的点位
        query_response = client.get("/api/v2/db/单元门点位?city=广州")
        query_data = json.loads(query_response.data)
        assert query_data["success"] is True
        assert query_data["pagination"]["total"] == 3
        
        # 2. 获取统计信息
        stats_response = client.get("/api/v2/db/stats/单元门点位")
        stats_data = json.loads(stats_response.data)
        assert stats_data["success"] is True
        assert stats_data["data"]["total_count"] == 5
        assert stats_data["data"]["city_stats"]["广州市"] == 3
    
    def test_search_then_query(self, client, setup_test_db):
        """测试先搜索再查询的流程"""
        # 1. 搜索包含"珠江"的记录
        search_response = client.get("/api/v2/db/search/单元门点位?q=珠江")
        search_data = json.loads(search_response.data)
        assert search_data["success"] is True
        assert search_data["total"] == 1
        
        # 2. 根据搜索结果中的城市进行精确查询
        first_result = search_data["data"][0]
        city = first_result["城市"]
        district = first_result["区域"]
        
        query_response = client.get(f"/api/v2/db/单元门点位?city={city}&district={district}")
        query_data = json.loads(query_response.data)
        assert query_data["success"] is True
        assert query_data["pagination"]["total"] >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
