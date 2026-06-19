"""
pDOOH Python 客户端库 - Tom Agent 客户端模块

封装 Tom Agent (端口 5003) 的所有端点接口。
"""

from typing import Any, Dict, List, Optional
import httpx

from .config import PDOOHConfig
from .exceptions import APIError, ConnectionError, TimeoutError
from .utils import parse_response, build_query_params


class TomAgentClient:
    """Tom Agent 客户端类。

    封装 Tom Agent 的所有端点接口，包括 CPM 跟踪、方案生成、
    城市列表、统计数据、竞品数据和汇总数据。

    Attributes:
        config: 客户端配置对象。
        client: httpx 客户端实例。
    """

    def __init__(self, config: Optional[PDOOHConfig] = None) -> None:
        """初始化 Tom Agent 客户端。

        Args:
            config: 客户端配置对象，如果为 None 则使用默认配置。
        """
        self.config = config if config is not None else PDOOHConfig()
        self._base_url = f"{self.config.base_url.rstrip('/')}:5003"
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
            raise ConnectionError(f"无法连接到 Tom Agent: {e}") from e
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

        检查 Tom Agent 服务是否正常运行。

        Returns:
            服务健康状态信息。
        """
        return self._request("GET", "/health")

    def track_cpm(
        self,
        campaign_id: str,
        impressions: int,
        clicks: int,
        spend: float,
    ) -> Dict[str, Any]:
        """CPM 跟踪。

        跟踪广告投放的 CPM（千次展示成本）数据。

        Args:
            campaign_id: 投放计划 ID。
            impressions: 展示量。
            clicks: 点击量。
            spend: 花费金额（元）。

        Returns:
            跟踪结果，包含 CPM、CTR 等指标。
        """
        json_data = {
            "campaign_id": campaign_id,
            "impressions": impressions,
            "clicks": clicks,
            "spend": spend,
        }
        return self._request("POST", "/api/cpm/track", json_data=json_data)

    def generate_plan(
        self,
        brand: str,
        budget: str,
        city: str,
        industry: str,
        target_audience: Optional[str] = None,
        duration_weeks: Optional[int] = None,
    ) -> Dict[str, Any]:
        """方案生成。

        根据品牌、预算、城市等参数生成广告投放方案。

        Args:
            brand: 品牌名称。
            budget: 预算，如 "30万"。
            city: 城市名称。
            industry: 行业分类。
            target_audience: 目标受众，可选。
            duration_weeks: 投放周期（周），可选。

        Returns:
            生成的投放方案，包含推荐点位、预算分配等。
        """
        json_data: Dict[str, Any] = {
            "brand": brand,
            "budget": budget,
            "city": city,
            "industry": industry,
        }
        if target_audience:
            json_data["target_audience"] = target_audience
        if duration_weeks:
            json_data["duration_weeks"] = duration_weeks
        return self._request("POST", "/api/plan/generate", json_data=json_data)

    def get_cities(self) -> Dict[str, Any]:
        """获取城市列表。

        获取支持投放的城市列表。

        Returns:
            城市列表数据。
        """
        return self._request("GET", "/api/cities")

    def get_stats(self) -> Dict[str, Any]:
        """获取统计数据。

        获取 Tom Agent 的统计数据，包括投放次数、覆盖城市等。

        Returns:
            统计数据。
        """
        return self._request("GET", "/api/stats")

    def get_competitors(
        self,
        industry: Optional[str] = None,
        city: Optional[str] = None,
    ) -> Dict[str, Any]:
        """获取竞品数据。

        获取指定行业和城市的竞品投放数据。

        Args:
            industry: 行业分类，可选。
            city: 城市名称，可选。

        Returns:
            竞品投放数据列表。
        """
        params = build_query_params(industry=industry, city=city)
        return self._request("GET", "/api/competitors", params=params)

    def get_summary(self) -> Dict[str, Any]:
        """获取汇总数据。

        获取所有投放数据的汇总信息。

        Returns:
            汇总数据。
        """
        return self._request("GET", "/api/summary")

    def close(self) -> None:
        """关闭 HTTP 客户端连接。"""
        self.client.close()

    def __enter__(self) -> "TomAgentClient":
        """上下文管理器入口。"""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """上下文管理器退出。"""
        self.close()
