"""
pDOOH Python 客户端库 - Tom Agent Client 单元测试

测试 TomAgentClient 类的所有方法。
"""

import unittest
from unittest.mock import Mock, patch
import httpx

from pdooh_client import TomAgentClient, PDOOHConfig
from pdooh_client.exceptions import APIError, ConnectionError, TimeoutError


class TestTomAgentClient(unittest.TestCase):
    """测试 TomAgentClient 类。"""

    def setUp(self) -> None:
        """测试前准备工作。"""
        self.config = PDOOHConfig(base_url="http://test.example.com")
        self.client = TomAgentClient(self.config)

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
    def test_generate_plan(self, mock_request: Mock) -> None:
        """测试 generate_plan 方法。"""
        # 模拟响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "plan_id": "123",
            "brand": "比亚迪",
            "recommendations": [],
        }
        mock_request.return_value = mock_response

        # 调用方法
        result = self.client.generate_plan(
            brand="比亚迪",
            budget="30万",
            city="广州",
            industry="汽车",
        )

        # 验证结果
        self.assertEqual(result["plan_id"], "123")
        self.assertEqual(result["brand"], "比亚迪")
        mock_request.assert_called_once()

    @patch("httpx.Client.request")
    def test_get_cities(self, mock_request: Mock) -> None:
        """测试 get_cities 方法。"""
        # 模拟响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "cities": ["广州", "深圳", "上海"],
        }
        mock_request.return_value = mock_response

        # 调用方法
        result = self.client.get_cities()

        # 验证结果
        self.assertIn("cities", result)
        self.assertEqual(len(result["cities"]), 3)
        mock_request.assert_called_once()

    @patch("httpx.Client.request")
    def test_get_competitors(self, mock_request: Mock) -> None:
        """测试 get_competitors 方法。"""
        # 模拟响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "competitors": [
                {"brand": "品牌A", "spend": 100000},
                {"brand": "品牌B", "spend": 200000},
            ],
        }
        mock_request.return_value = mock_response

        # 调用方法
        result = self.client.get_competitors(industry="汽车")

        # 验证结果
        self.assertIn("competitors", result)
        self.assertEqual(len(result["competitors"]), 2)
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
