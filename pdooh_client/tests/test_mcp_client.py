"""
pDOOH Python 客户端库 - MCP Client 单元测试

测试 MCPClient 类的所有方法。
"""

import unittest
from unittest.mock import Mock, patch
import httpx

from pdooh_client import MCPClient, PDOOHConfig
from pdooh_client.exceptions import APIError, ConnectionError, TimeoutError


class TestMCPClient(unittest.TestCase):
    """测试 MCPClient 类。"""

    def setUp(self) -> None:
        """测试前准备工作。"""
        self.config = PDOOHConfig(base_url="http://test.example.com")
        self.client = MCPClient(self.config)

    def tearDown(self) -> None:
        """测试后清理工作。"""
        self.client.close()

    @patch("httpx.Client.post")
    def test_query_screens(self, mock_post: Mock) -> None:
        """测试 query_screens 方法。"""
        # 模拟响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "screens": [{"id": "1", "name": "测试屏幕"}],
            "total": 1,
        }
        mock_post.return_value = mock_response

        # 调用方法
        result = self.client.query_screens(
            city="广州",
            district="天河区",
            min_house_price=8,
            tags=["母婴"],
            limit=10,
        )

        # 验证结果
        self.assertIn("screens", result)
        mock_post.assert_called_once()

    @patch("httpx.Client.post")
    def test_create_campaign(self, mock_post: Mock) -> None:
        """测试 create_campaign 方法。"""
        # 模拟响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "campaign_id": "123",
            "name": "测试计划",
        }
        mock_post.return_value = mock_response

        # 调用方法
        result = self.client.create_campaign(
            name="测试计划",
            brand="测试品牌",
            budget=100000.0,
            start_date="2024-01-01",
            end_date="2024-01-31",
            target_cities=["广州"],
        )

        # 验证结果
        self.assertEqual(result["campaign_id"], "123")
        mock_post.assert_called_once()

    @patch("httpx.Client.post")
    def test_calc_roi(self, mock_post: Mock) -> None:
        """测试 calc_roi 方法。"""
        # 模拟响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "roi": 1.5,
            "break_even_point": 50000,
        }
        mock_post.return_value = mock_response

        # 调用方法
        result = self.client.calc_roi(
            frames=1000,
            period_weeks=2,
            category="日化用品",
            media_type="unit_door",
            price_type="exchange",
        )

        # 验证结果
        self.assertEqual(result["roi"], 1.5)
        mock_post.assert_called_once()

    def test_timeout_error(self) -> None:
        """测试超时错误处理。"""
        with patch("httpx.Client.post") as mock_post:
            mock_post.side_effect = httpx.TimeoutException("请求超时")

            with self.assertRaises(TimeoutError):
                self.client.query_screens(city="广州")

    def test_connection_error(self) -> None:
        """测试连接错误处理。"""
        with patch("httpx.Client.post") as mock_post:
            mock_post.side_effect = httpx.ConnectError("连接失败")

            with self.assertRaises(ConnectionError):
                self.client.query_screens(city="广州")


if __name__ == "__main__":
    unittest.main()
