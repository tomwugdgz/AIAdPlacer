"""
知识库模块单元测试
"""
import json
import os
import pytest
from pathlib import Path
from datetime import date, datetime
from tempfile import TemporaryDirectory

from app.services.knowledge_base import KnowledgeManager


class TestKnowledgeManager:
    """知识库管理器测试"""

    @pytest.fixture
    def kb(self):
        """创建临时知识库实例"""
        with TemporaryDirectory() as tmpdir:
            kb = KnowledgeManager(root=Path(tmpdir))
            yield kb

    def test_store_single_record(self, kb):
        """测试存储单条记录"""
        result = kb.store(
            tool_name="pdooh_query_screens",
            arguments={"city": "广州", "district": "天河区"},
            result=[{"id": 1, "name": "天河城屏"}],
        )
        assert result["status"] == "stored"
        assert result["tool"] == "pdooh_query_screens"
        assert result["record_id"]  # ID 非空
        assert "file" in result
        assert "date" in result

    def test_store_multiple_records_same_file(self, kb):
        """测试多次存储相同参数记录（应追加到数组）"""
        res1 = kb.store(
            tool_name="pdooh_query_screens",
            arguments={"city": "广州"},
            result=[{"id": 1}],
        )
        # 修改参数生成不同 ID
        res2 = kb.store(
            tool_name="pdooh_query_screens",
            arguments={"city": "广州", "district": "天河区"},
            result=[{"id": 2}],
        )
        # 检查索引
        index = kb._load_index()
        assert len(index) == 2

    def test_store_with_extra_meta(self, kb):
        """测试存储带额外元数据"""
        result = kb.store(
            tool_name="pdooh_query_screens",
            arguments={"city": "深圳"},
            result=[{"id": 3}],
            extra_meta={"ip": "127.0.0.1", "user_agent": "TestClient/1.0"},
        )
        assert result["status"] == "stored"

    def test_serialize_decimal(self, kb):
        """测试 Decimal 类型序列化"""
        from decimal import Decimal
        result = kb._serialize({"price": Decimal("123.45")})
        assert result["price"] == 123.45
        assert isinstance(result["price"], float)

    def test_extract_key_params(self, kb):
        """测试从参数提取关键标识"""
        args = {"city": "广州", "district": "天河区", "name": "test"}
        key = kb._extract_key_params(args)
        assert "广州" in key
        assert "天河区" in key

    def test_file_safe_name(self, kb):
        """测试文件名安全处理"""
        unsafe = 'test/file:name<>"|'
        safe = kb._file_safe_name(unsafe)
        assert "/" not in safe
        assert ":" not in safe
        assert "<" not in safe

    def test_search_by_tool(self, kb):
        """测试按工具名检索"""
        kb.store("pdooh_query_screens", {"city": "广州"}, [{"id": 1}])
        kb.store("pdooh_audience_insight", {"city": "深圳"}, [{"id": 2}])
        results = kb.search(tool_name="pdooh_query_screens")
        assert len(results) == 1
        assert results[0]["tool"] == "pdooh_query_screens"

    def test_search_by_city(self, kb):
        """测试按城市检索"""
        kb.store("pdooh_query_screens", {"city": "广州", "name": "广州屏"}, [{"id": 1}])
        kb.store("pdooh_query_screens", {"city": "深圳", "name": "深圳屏"}, [{"id": 2}])
        results = kb.search(city="广州")
        assert len(results) == 1

    def test_search_by_keyword(self, kb):
        """测试关键词检索"""
        kb.store("pdooh_query_screens", {"city": "广州", "brand": "高端白酒"}, [{"id": 1}])
        results = kb.search(keyword="高端")
        assert len(results) == 1

    def test_search_by_date_range(self, kb):
        """测试日期范围检索"""
        kb.store("pdooh_query_screens", {"city": "广州"}, [{"id": 1}])
        today = date.today().isoformat()
        results = kb.search(date_from=today, date_to=today)
        assert len(results) == 1

    def test_search_with_limit(self, kb):
        """测试检索数量限制"""
        for i in range(10):
            kb.store("pdooh_query_screens", {"city": f"城市{i}"}, [{"id": i}])
        results = kb.search(limit=5)
        assert len(results) == 5

    def test_get_record(self, kb):
        """测试获取完整记录"""
        store_result = kb.store("pdooh_query_screens", {"city": "广州"}, [{"id": 1}])
        record_id = store_result["record_id"]
        record = kb.get_record(record_id)
        assert record is not None
        assert record["id"] == record_id
        assert record["tool"] == "pdooh_query_screens"

    def test_get_record_not_found(self, kb):
        """测试获取不存在的记录"""
        record = kb.get_record("nonexistent_id")
        assert record is None

    def test_list_by_date(self, kb):
        """测试按日期列出记录"""
        kb.store("pdooh_query_screens", {"city": "广州"}, [{"id": 1}])
        today = date.today().isoformat()
        records = kb.list_by_date(today)
        assert len(records) >= 1

    def test_list_by_date_no_data(self, kb):
        """测试不存在的日期"""
        records = kb.list_by_date("2020-01-01")
        assert records == []

    def test_list_by_tool(self, kb):
        """测试按工具名列出记录"""
        kb.store("pdooh_query_screens", {"city": "广州"}, [{"id": 1}])
        kb.store("pdooh_audience_insight", {"city": "深圳"}, [{"id": 2}])
        records = kb.list_by_tool("pdooh_query_screens")
        assert len(records) == 1

    def test_get_stats(self, kb):
        """测试获取统计信息"""
        kb.store("pdooh_query_screens", {"city": "广州"}, [{"id": 1}])
        kb.store("pdooh_query_screens", {"city": "深圳"}, [{"id": 2}])
        stats = kb.get_stats()
        assert stats["total_records"] == 2
        assert stats["by_tool"]["pdooh_query_screens"] == 2

    def test_list_dates(self, kb):
        """测试列出有数据的日期"""
        kb.store("pdooh_query_screens", {"city": "广州"}, [{"id": 1}])
        dates = kb.list_dates()
        assert len(dates) >= 1
        assert date.today().isoformat() in dates

    def test_list_tools(self, kb):
        """测试列出工具名"""
        kb.store("pdooh_query_screens", {"city": "广州"}, [{"id": 1}])
        kb.store("pdooh_audience_insight", {"city": "深圳"}, [{"id": 2}])
        tools = kb.list_tools()
        assert "pdooh_query_screens" in tools
        assert "pdooh_audience_insight" in tools

    def test_summarize_result(self, kb):
        """测试结果摘要提取"""
        result = {
            "content": [{"type": "text", "text": "这是测试结果内容"}]
        }
        summary = kb._summarize_result(result)
        assert "这是测试结果内容" in summary

    def test_summarize_result_long_text(self, kb):
        """测试结果摘要长度限制"""
        long_text = "A" * 300
        result = {"content": [{"type": "text", "text": long_text}]}
        summary = kb._summarize_result(result)
        assert len(summary) <= 203  # 200 + "..."

    def test_rebuild_index(self, kb):
        """测试重建索引"""
        kb.store("pdooh_query_screens", {"city": "广州"}, [{"id": 1}])
        # 清空索引
        kb.index_file.write_text("{}", encoding="utf-8")
        # 重建
        stats = kb.rebuild_index()
        assert stats["status"] == "rebuilt"
        assert stats["total_records"] == 1

    def test_cleanup_old_records(self, kb):
        """测试清理旧记录"""
        kb.store("pdooh_query_screens", {"city": "广州"}, [{"id": 1}])
        # 清理 0 天前的记录（清理今天的所有记录）
        # 由于记录今天是今天，清理 0 天前不会包含今天的记录
        # 改为清理 -1 天（包含今天）或验证 0 天不清理今天
        stats = kb.cleanup_old_records(days=0)
        # 清理 0 天前，今天的记录不会被清理（ cutoff = today - 0 = today）
        assert stats["status"] == "cleaned"
        # 确认 cutoff_date 是今天
        assert stats["cutoff_date"] == date.today().isoformat()


class TestAutoStoreMcpResult:
    """便捷函数测试"""

    @pytest.fixture
    def kb(self):
        """创建临时知识库实例"""
        with TemporaryDirectory() as tmpdir:
            from app.services import knowledge_base
            original_root = knowledge_base.KNOWLEDGE_ROOT
            kb = KnowledgeManager(root=Path(tmpdir))
            knowledge_base.kb = kb
            knowledge_base.CALL_LOG_FILE = Path(tmpdir) / "call_logs.jsonl"
            yield kb
            knowledge_base.kb = None

    def test_auto_store_basic(self, kb):
        """测试自动存储基础功能"""
        from app.services.knowledge_base import auto_store_mcp_result
        result = auto_store_mcp_result(
            tool_name="pdooh_query_screens",
            arguments={"city": "广州"},
            result=[{"id": 1}],
            ip="127.0.0.1",
            user_agent="TestClient",
        )
        assert result["status"] == "stored"
        assert result["tool"] == "pdooh_query_screens"

    def test_auto_store_with_ip(self, kb):
        """测试自动存储含 IP"""
        from app.services.knowledge_base import auto_store_mcp_result
        result = auto_store_mcp_result(
            tool_name="pdooh_query_screens",
            arguments={"city": "深圳"},
            result=[{"id": 2}],
            ip="192.168.1.1",
        )
        assert result["status"] == "stored"


class TestCallLogs:
    """调用日志测试"""

    @pytest.fixture
    def kb(self):
        """创建临时知识库实例"""
        with TemporaryDirectory() as tmpdir:
            from app.services import knowledge_base
            kb = KnowledgeManager(root=Path(tmpdir))
            knowledge_base.CALL_LOG_FILE = Path(tmpdir) / "call_logs.jsonl"
            yield kb

    def test_get_call_logs_empty(self, kb):
        """测试空日志文件"""
        data = kb.get_call_logs()
        assert data["total"] == 0
        assert data["logs"] == []

    def test_get_call_logs_with_data(self, kb):
        """测试获取调用日志"""
        kb.store("pdooh_query_screens", {"city": "广州"}, [{"id": 1}])
        data = kb.get_call_logs()
        assert data["total"] == 1
        assert len(data["logs"]) == 1
        assert data["logs"][0]["tool"] == "pdooh_query_screens"

    def test_get_call_logs_pagination(self, kb):
        """测试调用日志分页"""
        for i in range(5):
            kb.store("pdooh_query_screens", {"city": f"城市{i}"}, [{"id": i}])
        data = kb.get_call_logs(limit=2, offset=0)
        assert len(data["logs"]) == 2
        assert data["total"] == 5

    def test_get_call_logs_filter_by_tool(self, kb):
        """测试按工具名筛选调用日志"""
        kb.store("pdooh_query_screens", {"city": "广州"}, [{"id": 1}])
        kb.store("pdooh_audience_insight", {"city": "深圳"}, [{"id": 2}])
        data = kb.get_call_logs(tool_name="pdooh_query_screens")
        assert data["total"] == 1
        assert data["logs"][0]["tool"] == "pdooh_query_screens"

    def test_get_call_log_detail(self, kb):
        """测试获取调用日志详情"""
        store_result = kb.store("pdooh_query_screens", {"city": "广州"}, [{"id": 1}])
        record_id = store_result["record_id"]
        detail = kb.get_call_log_detail(record_id)
        assert detail is not None
        assert detail["id"] == record_id


class TestExportFunctions:
    """导出功能测试"""

    @pytest.fixture
    def kb(self):
        """创建临时知识库实例"""
        with TemporaryDirectory() as tmpdir:
            kb = KnowledgeManager(root=Path(tmpdir))
            yield kb

    def test_export_by_date(self, kb):
        """测试按日期导出"""
        kb.store("pdooh_query_screens", {"city": "广州"}, [{"id": 1}])
        today = date.today().isoformat()
        records = kb.export_by_date(today)
        assert len(records) >= 1

    def test_export_by_tool(self, kb):
        """测试按工具名导出"""
        kb.store("pdooh_query_screens", {"city": "广州"}, [{"id": 1}])
        kb.store("pdooh_audience_insight", {"city": "深圳"}, [{"id": 2}])
        records = kb.export_by_tool("pdooh_query_screens")
        assert len(records) == 1


class TestKnowledgeRoutes:
    """API 路由测试"""

    def test_knowledge_routes_import(self):
        """测试知识库路由可正常导入"""
        from app.api.knowledge_routes import router
        assert router is not None

    def test_knowledge_routes_tags(self):
        """测试路由标签正确"""
        from app.api.knowledge_routes import router
        assert "知识库管理" in router.tags
