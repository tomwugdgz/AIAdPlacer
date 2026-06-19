"""
pDOOH Python 客户端库 - ROI Agent Client 单元测试

测试 ROIAgentClient 类的所有方法。
"""

import unittest
from unittest.mock import Mock, patch
import httpx

from pdooh_client import ROIAgentClient, PDOOHConfig
from pdooh_client.exceptions import APIError, ConnectionError, TimeoutError


class TestROIAgentClient(unittest.TestCase):
    """测试 ROIAgentClient 类。"""

    def setUp(self) -> None:
        """测试前准备工作。"""
        self.config = PDOOHConfig(base_url="http://test.example.com")
        self.client = ROIAgentClient(self.config)

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
    def test_calc_roi(self, mock_request: Mock) -> None:
        """测试 calc_roi 方法。"""
        # 模拟响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "roi": 2.5,
            "break_even_point": 30000,
            "recommendations": [],
        }
        mock_request.return_value = mock_response

        # 调用方法
        result = self.client.calc_roi(
            frames=1000,
            period_weeks=2,
            category="日化用品",
            media_type="unit_door",
            price_type="exchange",
        )

        # 验证结果
        self.assertEqual(result["roi"], 2.5)
        self.assertEqual(result["break_even_point"], 30000)
        mock_request.assert_called_once()

    @patch("httpx.Client.request")
    def test_calc_three_scenarios(self, mock_request: Mock) -> None:
        """测试 calc_three_scenarios 方法。"""
        # 模拟响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "conservative": {"roi": 1.2},
            "neutral": {"roi": 2.0},
            "optimistic": {"roi": 3.5},
        }
        mock_request.return_value = mock_response

        # 调用方法
        result = self.client.calc_three_scenarios(
            n=1000,
            cost=130000,
            city="广州",
            product="日化",
        )

        # 验证结果
        self.assertIn("conservative", result)
        self.assertIn("neutral", result)
        self.assertIn("optimistic", result)
        mock_request.assert_called_once()

    @patch("httpx.Client.request")
    def test_get_categories(self, mock_request: Mock) -> None:
        """测试 get_categories 方法。"""
        # 模拟响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "categories": [
                {"name": "日化用品", "params": {}},
                {"name": "食品饮料", "params": {}},
            ],
        }
        mock_request.return_value = mock_response

        # 调用方法
        result = self.client.get_categories()

        # 验证结果
        self.assertIn("categories", result)
        self.assertEqual(len(result["categories"]), 2)
        mock_request.assert_called_once()

    @patch("httpx.Client.request")
    def test_get_formula(self, mock_request: Mock) -> None:
        """测试 get_formula 方法。"""
        # 模拟响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "formula": "ROI = (收益 - 成本) / 成本",
            "params": {},
        }
        mock_request.return_value = mock_response

        # 调用方法
        result = self.client.get_formula()

        # 验证结果
        self.assertIn("formula", result)
        mock_request.assert_called_once()

    def test_timeout_error(self) -> None:
        """测试超时错误处理。"""
        with patch("httpx.Client.request") as mock_request:
            mock_request.side_effect = httpx.TimeoutException("请求超时")

            with self.assertRaises(TimeoutError):
                self.client.calc_roi(
                    frames=1000,
                    period_weeks=2,
                    category="日化用品",
                    media_type="unit_door",
                    price_type="exchange",
                )

    def test_connection_error(self) -> None:
        """测试连接错误处理。"""
        with patch("httpx.Client.request") as mock_request:
            mock_request.side_effect = httpx.ConnectError("连接失败")

            with self.assertRaises(ConnectionError):
                self.client.health_check()


if __name__ == "__main__":
    unittest.main()
