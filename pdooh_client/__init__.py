"""
pDOOH Python 客户端库

统一的 pDOOH API 客户端库，封装 MCP Server、Tom Agent、ROI Agent 和竞品 Agent 的所有接口。
"""

from typing import Optional, Dict, Any

from .config import PDOOHConfig
from .exceptions import (
    PDOOHError,
    APIError,
    ConnectionError,
    TimeoutError,
    ValidationError,
    ConfigurationError,
)
from .mcp_client import MCPClient
from .tom_agent_client import TomAgentClient
from .roi_agent_client import ROIAgentClient
from .competitor_agent_client import CompetitorAgentClient
from .utils import parse_response, build_query_params


class PDOOHClient:
    """pDOOH 统一客户端类。

    提供统一入口访问所有 pDOOH 服务的 API，包括 MCP Server、Tom Agent、
    ROI Agent 和竞品 Agent。

    示例:
        >>> from pdooh_client import PDOOHClient
        >>> client = PDOOHClient(base_url="http://47.253.159.62")
        >>>
        >>> # 查询智能屏
        >>> screens = client.mcp.query_screens(city="广州", limit=10)
        >>>
        >>> # 计算 ROI
        >>> roi_result = client.roi.calc_roi(
        ...     frames=1000,
        ...     period_weeks=2,
        ...     category="日化用品",
        ...     media_type="unit_door",
        ...     price_type="exchange"
        ... )
        >>>
        >>> # 生成方案
        >>> plan = client.tom.generate_plan(
        ...     brand="比亚迪",
        ...     budget="30万",
        ...     city="广州",
        ...     industry="汽车"
        ... )
        >>>
        >>> # 查询竞品
        >>> competitors = client.competitor.get_competitors()

    Attributes:
        config: 客户端配置对象。
        mcp: MCP Server 客户端实例。
        tom: Tom Agent 客户端实例。
        roi: ROI Agent 客户端实例。
        competitor: 竞品 Agent 客户端实例。
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None,
        verify_ssl: Optional[bool] = None,
    ) -> None:
        """初始化 pDOOH 统一客户端。

        Args:
            base_url: API 服务器基础 URL，默认 http://47.253.159.62。
            timeout: HTTP 请求超时时间（秒），默认 30 秒。
            max_retries: 请求失败后的最大重试次数，默认 3 次。
            verify_ssl: 是否验证 SSL 证书，默认 True。

        示例:
            >>> client = PDOOHClient(base_url="http://47.253.159.62", timeout=60)
        """
        self.config = PDOOHConfig(
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            verify_ssl=verify_ssl,
        )
        self.mcp = MCPClient(self.config)
        self.tom = TomAgentClient(self.config)
        self.roi = ROIAgentClient(self.config)
        self.competitor = CompetitorAgentClient(self.config)

    def health_check_all(self) -> Dict[str, Any]:
        """检查所有服务的健康状态。

        Returns:
            包含所有服务健康状态结果的字典。
        """
        results = {}
        services = [
            ("mcp", self.mcp),
            ("tom", self.tom),
            ("roi", self.roi),
            ("competitor", self.competitor),
        ]

        for name, service in services:
            try:
                results[name] = service.health_check()
            except Exception as e:
                results[name] = {"status": "error", "message": str(e)}

        return results

    def close(self) -> None:
        """关闭所有客户端连接。"""
        self.mcp.close()
        self.tom.close()
        self.roi.close()
        self.competitor.close()

    def __enter__(self) -> "PDOOHClient":
        """上下文管理器入口。"""
        return self

    def __exit__(self, exc_type: Optional[type], exc_val: Optional[Exception],
                 exc_tb: Optional[Any]) -> None:
        """上下文管理器退出。"""
        self.close()


__all__ = [
    "PDOOHClient",
    "PDOOHConfig",
    "MCPClient",
    "TomAgentClient",
    "ROIAgentClient",
    "CompetitorAgentClient",
    "PDOOHError",
    "APIError",
    "ConnectionError",
    "TimeoutError",
    "ValidationError",
    "ConfigurationError",
    "parse_response",
    "build_query_params",
]
