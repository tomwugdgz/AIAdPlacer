"""
pDOOH Python 客户端库 - 竞品 Agent Client 单元测试

测试 CompetitorAgentClient 类的所有方法。
"""

import unittest
from unittest.mock import Mock, patch
import httpx

from pdooh_client import CompetitorAgentClient, PDOOHConfig
from pdooh_client.exceptions import APIError, ConnectionError, TimeoutError


class TestCompetitorAgentClient(unittest.TestCase):
    """测试 CompetitorAgentClient 类。"""

    def setUp(self) -> None:
        """测试前准备工作。"""
        self.config = PDOOHConfig(base_url="http://test.example.com")
        self.client = CompetitorAgentClient(self.config)

    def tearDown(self) -> None:
        """测试后清理工作。"""
        self.client.close()

    @patch("httpx.Client.request")
    def test_health_check(self, mock_request: Mock) -> None:
        """测试 health_check 方法。"""
        # 模拟响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "healthy"}
        mock_request.return_value = mock_response

        # 调用方法
        result = self.client.health_check()

        # 验证结果
        self.assertEqual(result["status"], "healthy")
        mock_request.assert_called_once()

    @patch("httpx.Client.request")
    def test_get_competitors(self, mock_request: Mock) -> None:
        """测试 get_competitors 方法。"""
        # 模拟响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "competitors": [
                {"brand": "品牌A", "industry": "汽车"},
                {"brand": "品牌B", "industry": "汽车"},
            ],
        }
        mock_request.return_value = mock_response

        # 调用方法
        result = self.client.get_competitors(industry="汽车")

        # 验证结果
        self.assertIn("competitors", result)
        self.assertEqual(len(result["competitors"]), 2)
        mock_request.assert_called_once()

    @patch("httpx.Client.request")
    def test_get_industries(self, mock_request: Mock) -> None:
        """测试 get_industries 方法。"""
        # 模拟响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "industries": ["汽车", "日化", "食品饮料", "房地产"],
        }
        mock_request.return_value = mock_response

        # 调用方法
        result = self.client.get_industries()

        # 验证结果
        self.assertIn("industries", result)
        self.assertEqual(len(result["industries"]), 4)
        mock_request.assert_called_once()

    @patch("httpx.Client.request")
    def test_search_intelligence(self, mock_request: Mock) -> None:
        """测试 search_intelligence 方法。"""
        # 模拟响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {"title": "比亚迪市场份额增长", "source": "行业报告"},
            ],
        }
        mock_request.return_value = mock_response

        # 调用方法
        result = self.client.search_intelligence(q="比亚迪")

        # 验证结果
        self.assertIn("results", result)
        self.assertEqual(len(result["results"]), 1)
        mock_request.assert_called_once()

    @patch("httpx.Client.request")
    def test_get_intelligence_stats(self, mock_request: Mock) -> None:
        """测试 get_intelligence_stats 方法。"""
        # 模拟响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "total": 1000,
            "by_industry": {"汽车": 200, "日化": 300},
        }
        mock_request.return_value = mock_response

        # 调用方法
        result = self.client.get_intelligence_stats()

        # 验证结果
        self.assertIn("total", result)
        self.assertIn("by_industry", result)
        mock_request.assert_called_once()

    def test_timeout_error(self) -> None:
        """测试超时错误处理。"""
        with patch("httpx.Client.request") as mock_request:
            mock_request.side_effect = httpx.TimeoutException("请求超时")

            with self.assertRaises(TimeoutError):
                self.client.health_check()

    def test_connection_error(self) -> None:
        """测试连接错误处理。"""
        with patch("httpx.Client.request") as mock_request:
            mock_request.side_effect = httpx.ConnectError("连接失败")

            with self.assertRaises(ConnectionError):
                self.client.health_check()


if __name__ == "__main__":
    unittest.main()
