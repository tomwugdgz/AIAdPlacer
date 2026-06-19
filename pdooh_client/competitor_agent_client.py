"""
pDOOH Python 客户端库 - 竞品 Agent 客户端模块

封装竞品 Agent (端口 5005) 的所有端点接口。
"""

from typing import Any, Dict, List, Optional
import httpx

from .config import PDOOHConfig
from .exceptions import APIError, ConnectionError, TimeoutError
from .utils import parse_response, build_query_params


class CompetitorAgentClient:
    """竞品 Agent 客户端类。

    封装竞品 Agent 的所有端点接口，包括竞品列表、重点品牌、
    行业分类、市场情报查询等。

    Attributes:
        config: 客户端配置对象。
        client: httpx 客户端实例。
    """

    def __init__(self, config: Optional[PDOOHConfig] = None) -> None:
        """初始化竞品 Agent 客户端。

        Args:
            config: 客户端配置对象，如果为 None 则使用默认配置。
        """
        self.config = config if config is not None else PDOOHConfig()
        self._base_url = f"{self.config.base_url.rstrip('/')}:5005"
        self.client = httpx.Client(
            base_url=self._base_url,
            timeout=self.config.timeout,
            verify=self.config.verify_ssl,
        )

    def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """发送 HTTP 请求。

        Args:
            method: HTTP 方法，如 "GET"、"POST"。
            path: API 路径。
            params: 查询参数，可选。
            json_data: JSON 请求体，可选。

        Returns:
            解析后的响应数据。

        Raises:
            APIError: 当 API 调用失败时抛出。
            ConnectionError: 当连接失败时抛出。
            TimeoutError: 当请求超时时抛出。
        """
        try:
            response = self.client.request(
                method=method,
                url=path,
                params=params,
                json=json_data,
            )
            response.raise_for_status()
            return parse_response(response)
        except httpx.TimeoutException as e:
            raise TimeoutError(f"请求 {path} 超时") from e
        except httpx.ConnectError as e:
            raise ConnectionError(f"无法连接到竞品 Agent: {e}") from e
        except httpx.HTTPStatusError as e:
            raise APIError(
                message=f"请求 {path} 失败: {e}",
                status_code=e.response.status_code,
                response=parse_response(e.response) if e.response else None,
            ) from e
        except Exception as e:
            raise APIError(f"请求 {path} 时发生未知错误: {e}") from e

    def health_check(self) -> Dict[str, Any]:
        """健康检查。

        检查竞品 Agent 服务是否正常运行。

        Returns:
            服务健康状态信息。
        """
        return self._request("GET", "/health")

    def get_competitors(
        self,
        industry: Optional[str] = None,
        city: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """获取竞品列表。

        获取竞品品牌列表，支持按行业和城市筛选。

        Args:
            industry: 行业分类，可选。
            city: 城市名称，可选。
            limit: 返回记录数量限制，可选。

        Returns:
            竞品品牌列表。
        """
        params = build_query_params(industry=industry, city=city, limit=limit)
        return self._request("GET", "/api/competitors", params=params)

    def get_brands(
        self,
        industry: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """获取重点品牌。

        获取重点监测的品牌列表。

        Args:
            industry: 行业分类，可选。
            limit: 返回记录数量限制，可选。

        Returns:
            重点品牌列表。
        """
        params = build_query_params(industry=industry, limit=limit)
        return self._request("GET", "/api/brands", params=params)

    def get_industries(self) -> Dict[str, Any]:
        """获取行业分类。

        获取所有支持的行业分类列表。

        Returns:
            行业分类列表。
        """
        return self._request("GET", "/api/industries")

    def get_intelligence(
        self,
        industry: str,
        city: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """获取市场情报。

        获取指定行业的市场情报数据。

        Args:
            industry: 行业分类。
            city: 城市名称，可选。
            limit: 返回记录数量限制，可选。

        Returns:
            市场情报数据列表。
        """
        params = build_query_params(industry=industry, city=city, limit=limit)
        return self._request("GET", "/api/intelligence", params=params)

    def get_intelligence_stats(self) -> Dict[str, Any]:
        """获取情报统计。

        获取市场情报的统计数据，包括各行业的情报数量等。

        Returns:
            情报统计数据。
        """
        return self._request("GET", "/api/intelligence/stats")

    def search_intelligence(
        self,
        q: str,
        industry: Optional[str] = None,
        city: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """搜索市场情报。

        根据关键词搜索市场情报数据。

        Args:
            q: 搜索关键词，如 "比亚迪"。
            industry: 行业分类，可选。
            city: 城市名称，可选。
            limit: 返回记录数量限制，可选。

        Returns:
            匹配的情报数据列表。
        """
        params = build_query_params(q=q, industry=industry, city=city, limit=limit)
        return self._request("GET", "/api/intelligence/search", params=params)

    def close(self) -> None:
        """关闭 HTTP 客户端连接。"""
        self.client.close()

    def __enter__(self) -> "CompetitorAgentClient":
        """上下文管理器入口。"""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """上下文管理器退出。"""
        self.close()
