"""
pDOOH Python 客户端库 - ROI Agent 客户端模块

封装 ROI Agent (端口 5004) 的所有端点接口。
"""

from typing import Any, Dict, List, Optional
import httpx

from .config import PDOOHConfig
from .exceptions import APIError, ConnectionError, TimeoutError
from .utils import parse_response, build_query_params


class ROIAgentClient:
    """ROI Agent 客户端类。

    封装 ROI Agent 的所有端点接口，包括 ROI 计算、三场景计算、
    品类参数查询、竞品对比和公式说明。

    Attributes:
        config: 客户端配置对象。
        client: httpx 客户端实例。
    """

    def __init__(self, config: Optional[PDOOHConfig] = None) -> None:
        """初始化 ROI Agent 客户端。

        Args:
            config: 客户端配置对象，如果为 None 则使用默认配置。
        """
        self.config = config if config is not None else PDOOHConfig()
        self._base_url = f"{self.config.base_url.rstrip('/')}:5004"
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
            raise ConnectionError(f"无法连接到 ROI Agent: {e}") from e
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

        检查 ROI Agent 服务是否正常运行。

        Returns:
            服务健康状态信息。
        """
        return self._request("GET", "/health")

    def calc_roi(
        self,
        frames: int,
        period_weeks: int,
        category: str,
        media_type: str,
        price_type: str,
        city: Optional[str] = None,
        product: Optional[str] = None,
        cpm: Optional[float] = None,
        reach: Optional[int] = None,
    ) -> Dict[str, Any]:
        """计算 ROI。

        计算社区营销投资的 ROI（投资回报率）。

        Args:
            frames: 屏幕数量（帧）。
            period_weeks: 投放周期（周）。
            category: 品类，如 "日化用品"。
            media_type: 媒体类型，如 "unit_door"、"dao_cha"、"led"。
            price_type: 价格类型，如 "exchange"（兑换价）、"retail"（零售价）。
            city: 城市名称，可选。
            product: 产品名称，可选。
            cpm: 自定义 CPM 值，可选。
            reach: 自定义触达人数，可选。

        Returns:
            ROI 计算结果，包含 ROI 值、盈亏平衡点、建议等。
        """
        json_data = {
            "frames": frames,
            "period_weeks": period_weeks,
            "category": category,
            "media_type": media_type,
            "price_type": price_type,
        }
        if city:
            json_data["city"] = city
        if product:
            json_data["product"] = product
        if cpm is not None:
            json_data["cpm"] = cpm
        if reach is not None:
            json_data["reach"] = reach
        return self._request("POST", "/api/roi", json_data=json_data)

    def calc_three_scenarios(
        self,
        n: int,
        cost: float,
        city: str,
        product: str,
    ) -> Dict[str, Any]:
        """三场景计算。

        计算三种不同场景（保守、中性、乐观）的 ROI。

        Args:
            n: 屏幕数量（帧）。
            cost: 总成本（元）。
            city: 城市名称。
            product: 产品名称/品类。

        Returns:
            三种场景的 ROI 计算结果。
        """
        params = {
            "N": n,
            "cost": cost,
            "city": city,
            "product": product,
        }
        return self._request("GET", "/api/v2/roi/three-scenarios", params=params)

    def get_categories(self) -> Dict[str, Any]:
        """获取品类参数。

        获取所有支持的品类和对应的参数配置。

        Returns:
            品类参数列表。
        """
        return self._request("GET", "/api/categories")

    def compare_competitors(
        self,
        brand: str,
        competitors: List[str],
        city: Optional[str] = None,
    ) -> Dict[str, Any]:
        """竞品对比。

        对比指定品牌与竞品的 ROI 表现。

        Args:
            brand: 本品牌名称。
            competitors: 竞品品牌列表。
            city: 城市名称，可选。

        Returns:
            对比结果，包含各品牌的 ROI 指标。
        """
        params = build_query_params(
            brand=brand,
            competitors=",".join(competitors) if competitors else None,
            city=city,
        )
        return self._request("GET", "/api/compare", params=params)

    def get_formula(self) -> Dict[str, Any]:
        """获取公式说明。

        获取 ROI 计算所使用的公式和参数说明。

        Returns:
            公式说明文档。
        """
        return self._request("GET", "/api/formula")

    def close(self) -> None:
        """关闭 HTTP 客户端连接。"""
        self.client.close()

    def __enter__(self) -> "ROIAgentClient":
        """上下文管理器入口。"""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """上下文管理器退出。"""
        self.close()
