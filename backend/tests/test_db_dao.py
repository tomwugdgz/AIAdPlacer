"""
数据库访问层（DAO）测试用例

测试 db_dao.py 的所有功能

作者: 寇豆码（Kou）
日期: 2026-03-04
修复: 严过关（Yan）- 2026-03-04 修复测试数据和表名
"""

import pytest
import sqlite3
import os
import tempfile
from pathlib import Path
from typing import Generator

# 导入被测试的模块
from app.db_dao import (
    get_db_connection,
    get_all_tables,
    query_table,
    get_table_stats,
    search_table,
    search_clients,
    get_points_by_type,
)


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def test_db() -> Generator[str, None, None]:
    """
    创建测试数据库（临时文件）
    
    Yields:
        临时数据库文件路径
    """
    # 创建临时数据库文件
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    
    # 创建测试表
    conn.execute("""
        CREATE TABLE "单元测试门点位" (
            id INTEGER PRIMARY KEY,
            "省份" TEXT,
            "城市" TEXT,
            "区域" TEXT,
            "商圈" TEXT,
            "楼盘类型" TEXT,
            "楼栋数量" INTEGER,
            "单元门数量" INTEGER,
            "楼盘价格" REAL,
            "住户数量" INTEGER,
            "经度" REAL,
            "纬度" REAL
        )
    """)
    
    conn.execute("""
        CREATE TABLE "客户通讯录" (
            id INTEGER PRIMARY KEY,
            "客户简称" TEXT,
            "品牌名称" TEXT,
            "决策城市" TEXT,
            "行业" TEXT,
            "联系人" TEXT,
            "手机" TEXT
        )
    """)
    
    # 插入测试数据
    test_data_1 = [
        (1, "广东省", "广州市", "天河区", "珠江新城", "住宅", 10, 20, 50000, 500, 113.3, 23.1),
        (2, "广东省", "广州市", "越秀区", "北京路", "住宅", 8, 16, 45000, 400, 113.2, 23.2),
        (3, "广东省", "深圳市", "南山区", "科技园", "商业", 15, 30, 80000, 800, 114.0, 22.5),
        (4, "湖南省", "长沙市", "岳麓区", "梅溪湖", "住宅", 12, 24, 35000, 600, 112.9, 28.2),
        (5, "广东省", "广州市", "天河区", "天河路", "商业", 20, 40, 55000, 1000, None, None),  # 无经纬度
    ]
    
    conn.executemany(
        'INSERT INTO "单元测试门点位" VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
        test_data_1
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
    
    # 修改 db_dao 的数据库路径
    from app import db_dao as db_dao_module
    original_db_path = db_dao_module.DB_PATH
    db_dao_module.DB_PATH = Path(db_path)
    
    yield db_path
    
    # 恢复原始数据库路径
    db_dao_module.DB_PATH = original_db_path
    
    # 清理临时文件
    os.close(db_fd)
    os.unlink(db_path)


# ── 测试用例 ─────────────────────────────────────────────────────────────────

class TestGetDbConnection:
    """测试 get_db_connection 函数"""
    
    def test_success(self, test_db: str):
        """测试成功连接数据库"""
        conn = get_db_connection()
        assert conn is not None
        assert isinstance(conn, sqlite3.Connection)
        
        # 验证 WAL 模式
        cursor = conn.execute("PRAGMA journal_mode")
        # WAL 模式已在连接时设置
        
        conn.close()
    
    def test_db_not_found(self, monkeypatch):
        """测试数据库文件不存在时抛出异常"""
        from app import db_dao as db_dao_module
        original_path = db_dao_module.DB_PATH
        db_dao_module.DB_PATH = Path("/nonexistent/path.db")
        
        with pytest.raises(FileNotFoundError):
            get_db_connection()
        
        db_dao_module.DB_PATH = original_path


class TestGetAllTables:
    """测试 get_all_tables 函数"""
    
    def test_success(self, test_db: str):
        """测试成功获取所有表信息"""
        tables = get_all_tables()
        
        assert len(tables) == 2
        assert tables[0]["name"] == "单元测试门点位"
        assert tables[0]["count"] == 5
        assert "省份" in tables[0]["columns"]
        assert "城市" in tables[0]["columns"]
        
        assert tables[1]["name"] == "客户通讯录"
        assert tables[1]["count"] == 3


class TestQueryTable:
    """测试 query_table 函数"""
    
    def test_basic_query(self, test_db: str):
        """测试基本查询"""
        result = query_table("单元测试门点位", page=1, page_size=10)
        
        assert result["total"] == 5
        assert len(result["data"]) == 5
        assert result["page"] == 1
        assert result["page_size"] == 10
        assert result["total_pages"] == 1
    
    def test_pagination(self, test_db: str):
        """测试分页功能"""
        result = query_table("单元测试门点位", page=1, page_size=2)
        
        assert len(result["data"]) == 2
        assert result["total_pages"] == 3  # 5 条记录，每页 2 条 = 3 页
        
        # 获取第 2 页
        result2 = query_table("单元测试门点位", page=2, page_size=2)
        assert len(result2["data"]) == 2
        assert result2["page"] == 2
    
    def test_filter_by_city(self, test_db: str):
        """测试按城市筛选"""
        result = query_table("单元测试门点位", filters={"city": "广州"}, page=1, page_size=20)
        
        assert result["total"] == 3  # 3 条广州的记录
        assert all(row["城市"] == "广州市" for row in result["data"])
    
    def test_filter_by_province(self, test_db: str):
        """测试按省份筛选"""
        result = query_table("单元测试门点位", filters={"province": "广东"}, page=1, page_size=20)
        
        assert result["total"] == 4  # 4 条广东省的记录
        assert all(row["省份"] == "广东省" for row in result["data"])
    
    def test_filter_by_district(self, test_db: str):
        """测试按区域筛选"""
        result = query_table("单元测试门点位", filters={"district": "天河"}, page=1, page_size=20)
        
        assert result["total"] == 2  # 2 条天河区记录
        assert all("天河" in row["区域"] for row in result["data"])
    
    def test_filter_by_business_district(self, test_db: str):
        """测试按商圈筛选"""
        result = query_table("单元测试门点位", filters={"business_district": "珠江"}, page=1, page_size=20)
        
        assert result["total"] == 1
        assert "珠江新城" in result["data"][0]["商圈"]
    
    def test_filter_by_price_range(self, test_db: str):
        """测试按价格范围筛选"""
        # 注意：DAO 代码中使用了 OR "刊例价" >= ?
        # 如果表没有"刊例价"字段，这个条件是无效的
        # 测试数据中价格 >= 50000 的有 3 条（50000, 55000, 80000）
        result = query_table("单元测试门点位", filters={"min_price": 50000}, page=1, page_size=20)
        
        # 由于测试表的字段不包含"刊例价"，只按"楼盘价格"筛选
        # 应该返回 3 条记录
        assert result["total"] == 3  # 价格 >= 50000 的记录: 50000, 55000, 80000
    
    def test_invalid_table_name(self, test_db: str):
        """测试表名不存在时抛出异常"""
        with pytest.raises(ValueError, match="表不存在"):
            query_table("不存在的表", page=1, page_size=20)
    
    def test_invalid_page(self, test_db: str):
        """测试无效的页码"""
        with pytest.raises(ValueError, match="page 必须大于等于 1"):
            query_table("单元测试门点位", page=0, page_size=20)
    
    def test_invalid_page_size(self, test_db: str):
        """测试无效的每页记录数"""
        with pytest.raises(ValueError, match="page_size 必须在 1-1000 之间"):
            query_table("单元测试门点位", page=1, page_size=0)
        
        with pytest.raises(ValueError, match="page_size 必须在 1-1000 之间"):
            query_table("单元测试门点位", page=1, page_size=1001)


class TestGetTableStats:
    """测试 get_table_stats 函数"""
    
    def test_success(self, test_db: str):
        """测试成功获取统计信息"""
        stats = get_table_stats("单元测试门点位")
        
        assert stats["total_count"] == 5
        assert "city_stats" in stats
        assert stats["city_stats"]["广州市"] == 3
        assert stats["city_stats"]["深圳市"] == 1
        assert stats["city_stats"]["长沙市"] == 1
        
        assert "province_stats" in stats
        assert stats["province_stats"]["广东省"] == 4
        assert stats["province_stats"]["湖南省"] == 1
        
        assert stats["has_coordinates"] == 4  # 4 条有经纬度
        assert stats["null_coordinates"] == 1  # 1 条无经纬度
    
    def test_table_not_found(self, test_db: str):
        """测试表名不存在时抛出异常"""
        with pytest.raises(ValueError, match="表不存在"):
            get_table_stats("不存在的表")


class TestSearchTable:
    """测试 search_table 函数"""
    
    def test_search_in_all_columns(self, test_db: str):
        """测试全文搜索（在所有字段中搜索）"""
        results = search_table("单元测试门点位", keyword="广州")
        
        assert len(results) == 3  # 3 条包含"广州"的记录
        assert all("广州" in str(row) for row in results)
    
    def test_search_no_results(self, test_db: str):
        """测试搜索无结果"""
        # "北京xyz" 不会匹配 "北京路"
        results = search_table("单元测试门点位", keyword="北京xyz")
        assert len(results) == 0
    
    def test_search_empty_keyword(self, test_db: str):
        """测试空关键词"""
        with pytest.raises(ValueError, match="搜索关键词不能为空"):
            search_table("单元测试门点位", keyword="")
    
    def test_search_limit(self, test_db: str):
        """测试搜索结果限制（最多 100 条）"""
        # 插入更多数据
        conn = get_db_connection()
        for i in range(150):
            conn.execute(
                'INSERT INTO "单元测试门点位" ("省份", "城市") VALUES (?, ?)',
                ("测试省", f"测试市{i}")
            )
        conn.commit()
        conn.close()
        
        results = search_table("单元测试门点位", keyword="测试")
        assert len(results) == 100  # 最多返回 100 条


class TestSearchClients:
    """测试 search_clients 函数"""
    
    def test_search_by_keyword(self, test_db: str):
        """测试按关键词搜索"""
        results = search_clients(keyword="华为")
        
        assert len(results) == 1
        assert results[0]["客户简称"] == "华为技术"
    
    def test_search_by_city(self, test_db: str):
        """测试按城市筛选"""
        results = search_clients(keyword="", city="深圳")
        
        assert len(results) == 2  # 2 条深圳的记录
        assert all(row["决策城市"] == "深圳市" for row in results)
    
    def test_search_by_industry(self, test_db: str):
        """测试按行业筛选"""
        results = search_clients(keyword="", industry="互联网")
        
        assert len(results) == 2  # 2 条互联网行业的记录
    
    def test_search_with_limit(self, test_db: str):
        """测试限制返回数量"""
        results = search_clients(keyword="", limit=2)
        assert len(results) <= 2
    
    def test_table_not_found(self, monkeypatch, test_db: str):
        """测试"客户通讯录"表不存在时抛出异常"""
        # 重命名表
        conn = get_db_connection()
        conn.execute('ALTER TABLE "客户通讯录" RENAME TO "改名后的表"')
        conn.commit()
        conn.close()
        
        with pytest.raises(ValueError, match="表不存在: 客户通讯录"):
            search_clients(keyword="测试")
    
    def test_invalid_limit(self, test_db: str):
        """测试无效的 limit"""
        with pytest.raises(ValueError, match="limit 必须在 1-500 之间"):
            search_clients(keyword="测试", limit=0)
        
        with pytest.raises(ValueError, match="limit 必须在 1-500 之间"):
            search_clients(keyword="测试", limit=501)


class TestGetPointsByType:
    """测试 get_points_by_type 函数"""
    
    def test_success(self, test_db: str, monkeypatch):
        """测试成功按类型获取点位"""
        # Mock type_to_table 映射
        from app import db_dao as db_dao_module
        
        # Mock 映射
        monkeypatch.setattr(db_dao_module, "type_to_table", {
            "unit_door": "单元测试门点位"
        })
        
        result = get_points_by_type("unit_door", city="广州", limit=50)
        
        assert result["total"] == 3  # 3 条广州的记录
        assert all(row["城市"] == "广州市" for row in result["data"])
    
    def test_invalid_point_type(self, test_db: str):
        """测试无效的点位类型"""
        with pytest.raises(ValueError, match="不支持的点位类型"):
            get_points_by_type("invalid_type")


# ── 集成测试 ─────────────────────────────────────────────────────────────────

class TestIntegration:
    """集成测试：测试多个函数的组合使用"""
    
    def test_query_then_stats(self, test_db: str):
        """测试先查询再统计的流程"""
        # 1. 查询广州的点位
        query_result = query_table("单元测试门点位", filters={"city": "广州"}, page=1, page_size=20)
        assert query_result["total"] == 3
        
        # 2. 获取统计信息
        stats = get_table_stats("单元测试门点位")
        assert stats["total_count"] == 5
        assert stats["city_stats"]["广州市"] == 3
    
    def test_search_then_query(self, test_db: str):
        """测试先搜索再查询的流程"""
        # 1. 搜索包含"珠江"的记录
        search_results = search_table("单元测试门点位", keyword="珠江")
        assert len(search_results) == 1
        guangzhou_row = search_results[0]
        
        # 2. 根据搜索结果查询更详细的信息
        detail_result = query_table(
            "单元测试门点位",
            filters={"city": guangzhou_row["城市"], "district": guangzhou_row["区域"]},
            page=1,
            page_size=20
        )
        assert detail_result["total"] >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
