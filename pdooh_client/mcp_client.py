"""
pDOOH Python 客户端库 - MCP Server 客户端模块

封装 MCP Server (端口 5002) 的所有 22 个工具调用接口。
"""

from typing import Any, Dict, List, Optional
import httpx

from .config import PDOOHConfig
from .exceptions import APIError, ConnectionError, TimeoutError
from .utils import parse_response, build_query_params


class MCPClient:
    """MCP Server 客户端类。

    封装 MCP Server 的所有 22 个工具调用接口，包括核心投放工具、
    本地数据库工具、点位查询工具、资源统计工具和 ROI 计算工具。

    Attributes:
        config: 客户端配置对象。
        client: httpx 客户端实例。
    """

    def __init__(self, config: Optional[PDOOHConfig] = None) -> None:
        """初始化 MCP Server 客户端。

        Args:
            config: 客户端配置对象，如果为 None 则使用默认配置。
        """
        self.config = config if config is not None else PDOOHConfig()
        self._base_url = f"{self.config.base_url.rstrip('/')}:5002"
        self.client = httpx.Client(
            base_url=self._base_url,
            timeout=self.config.timeout,
            verify=self.config.verify_ssl,
        )

    def _call_tool(
        self, tool_name: str, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """调用 MCP 工具。

        Args:
            tool_name: 工具名称。
            arguments: 工具参数。

        Returns:
            工具调用的响应数据。

        Raises:
            APIError: 当 API 调用失败时抛出。
            ConnectionError: 当连接失败时抛出。
            TimeoutError: 当请求超时时抛出。
        """
        try:
            response = self.client.post(
                "/api/v2/mcp/pdooh/tools/call",
                json={"name": tool_name, "arguments": arguments},
            )
            response.raise_for_status()
            return parse_response(response)
        except httpx.TimeoutException as e:
            raise TimeoutError(f"调用工具 {tool_name} 超时") from e
        except httpx.ConnectError as e:
            raise ConnectionError(f"无法连接到 MCP Server: {e}") from e
        except httpx.HTTPStatusError as e:
            raise APIError(
                message=f"工具 {tool_name} 调用失败: {e}",
                status_code=e.response.status_code,
                response=parse_response(e.response) if e.response else None,
            ) from e
        except Exception as e:
            raise APIError(f"工具 {tool_name} 调用时发生未知错误: {e}") from e

    # ==================== 1.1 核心投放工具 ====================

    def query_screens(
        self,
        city: Optional[str] = None,
        district: Optional[str] = None,
        min_house_price: Optional[float] = None,
        tags: Optional[List[str]] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """查询智能屏。

        核心投放工具 1/7：根据城市、区域、房价、标签等条件查询智能屏资源。

        Args:
            city: 城市名称，如 "广州"。
            district: 区名称，如 "天河区"。
            min_house_price: 最小房价（万元），如 8 表示房价 8 万以上。
            tags: 标签列表，如 ["母婴", "美妆"]。
            limit: 返回记录数量限制，默认 20。
            offset: 偏移量，默认 0。

        Returns:
            智能屏查询结果，包含屏幕列表和总数。
        """
        arguments = build_query_params(
            city=city,
            district=district,
            min_house_price=min_house_price,
            tags=tags,
            limit=limit,
            offset=offset,
        )
        return self._call_tool("pdooh_query_screens", arguments)

    def get_screen_audience(
        self,
        screen_id: str,
    ) -> Dict[str, Any]:
        """获取屏人群画像。

        核心投放工具 2/7：获取指定智能屏的人群画像数据。

        Args:
            screen_id: 智能屏 ID。

        Returns:
            人群画像数据，包含年龄分布、性别比例、消费能力等。
        """
        arguments = {"screen_id": screen_id}
        return self._call_tool("pdooh_get_screen_audience", arguments)

    def create_campaign(
        self,
        name: str,
        brand: str,
        budget: float,
        start_date: str,
        end_date: str,
        target_cities: List[str],
        screen_ids: Optional[List[str]] = None,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """创建投放计划。

        核心投放工具 3/7：创建新的广告投放计划。

        Args:
            name: 投放计划名称。
            brand: 品牌名称。
            budget: 投放预算（元）。
            start_date: 开始日期，格式 "YYYY-MM-DD"。
            end_date: 结束日期，格式 "YYYY-MM-DD"。
            target_cities: 目标城市列表。
            screen_ids: 指定屏幕 ID 列表，可选。
            description: 计划描述，可选。

        Returns:
            创建的投放计划信息，包含计划 ID。
        """
        arguments: Dict[str, Any] = {
            "name": name,
            "brand": brand,
            "budget": budget,
            "start_date": start_date,
            "end_date": end_date,
            "target_cities": target_cities,
        }
        if screen_ids:
            arguments["screen_ids"] = screen_ids
        if description:
            arguments["description"] = description
        return self._call_tool("pdooh_create_campaign", arguments)

    def query_campaigns(
        self,
        campaign_id: Optional[str] = None,
        brand: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """查询投放计划。

        核心投放工具 4/7：查询已创建的投放计划列表或详情。

        Args:
            campaign_id: 投放计划 ID，指定时返回详情。
            brand: 按品牌筛选。
            status: 按状态筛选，如 "active"、"paused"、"completed"。
            limit: 返回记录数量限制，默认 20。
            offset: 偏移量，默认 0。

        Returns:
            投放计划列表或详情。
        """
        arguments = build_query_params(
            campaign_id=campaign_id,
            brand=brand,
            status=status,
            limit=limit,
            offset=offset,
        )
        return self._call_tool("pdooh_query_campaigns", arguments)

    def submit_creative(
        self,
        campaign_id: str,
        creative_type: str,
        file_url: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """提交创意。

        核心投放工具 5/7：为投放计划提交广告创意素材。

        Args:
            campaign_id: 投放计划 ID。
            creative_type: 创意类型，如 "image"、"video"、"html5"。
            file_url: 素材文件 URL。
            title: 创意标题，可选。
            description: 创意描述，可选。

        Returns:
            提交结果，包含创意 ID 和审核状态。
        """
        arguments: Dict[str, Any] = {
            "campaign_id": campaign_id,
            "creative_type": creative_type,
            "file_url": file_url,
        }
        if title:
            arguments["title"] = title
        if description:
            arguments["description"] = description
        return self._call_tool("pdooh_submit_creative", arguments)

    def query_report(
        self,
        campaign_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        metrics: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """查询投放报告。

        核心投放工具 6/7：查询指定投放计划的投放数据报告。

        Args:
            campaign_id: 投放计划 ID。
            start_date: 开始日期，格式 "YYYY-MM-DD"，可选。
            end_date: 结束日期，格式 "YYYY-MM-DD"，可选。
            metrics: 指定指标列表，如 ["impressions", "clicks", "reach"]，可选。

        Returns:
            投放数据报告，包含展示量、点击量、触达人数等指标。
        """
        arguments: Dict[str, Any] = {"campaign_id": campaign_id}
        if start_date:
            arguments["start_date"] = start_date
        if end_date:
            arguments["end_date"] = end_date
        if metrics:
            arguments["metrics"] = metrics
        return self._call_tool("pdooh_query_report", arguments)

    def compliance_check(
        self,
        creative_id: str,
        creative_type: str,
        file_url: str,
    ) -> Dict[str, Any]:
        """合规审核。

        核心投放工具 7/7：对广告创意进行合规审核。

        Args:
            creative_id: 创意 ID。
            creative_type: 创意类型。
            file_url: 素材文件 URL。

        Returns:
            审核结果，包含是否通过、不通过原因等。
        """
        arguments = {
            "creative_id": creative_id,
            "creative_type": creative_type,
            "file_url": file_url,
        }
        return self._call_tool("pdooh_compliance_check", arguments)

    # ==================== 1.2 本地数据库工具 ====================

    def query_local_screens(
        self,
        city: Optional[str] = None,
        district: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """查询本地屏幕。

        本地数据库工具 1/4：查询本地数据库中的屏幕资源。

        Args:
            city: 城市名称。
            district: 区名称。
            limit: 返回记录数量限制，默认 20。
            offset: 偏移量，默认 0。

        Returns:
            本地屏幕查询结果。
        """
        arguments = build_query_params(
            city=city,
            district=district,
            limit=limit,
            offset=offset,
        )
        return self._call_tool("pdooh_query_local_screens", arguments)

    def query_local_stats(
        self,
        city: Optional[str] = None,
    ) -> Dict[str, Any]:
        """查询本地统计。

        本地数据库工具 2/4：查询本地数据库的统计信息。

        Args:
            city: 城市名称，可选。

        Returns:
            统计数据，包含屏幕数量、覆盖社区数等。
        """
        arguments = build_query_params(city=city)
        return self._call_tool("pdooh_query_local_stats", arguments)

    def search_local_community(
        self,
        keyword: str,
        city: Optional[str] = None,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """搜索楼盘。

        本地数据库工具 3/4：根据关键词搜索社区/楼盘信息。

        Args:
            keyword: 搜索关键词。
            city: 城市名称，可选。
            limit: 返回记录数量限制，默认 20。

        Returns:
            匹配的社区/楼盘列表。
        """
        arguments: Dict[str, Any] = {"keyword": keyword}
        if city:
            arguments["city"] = city
        arguments["limit"] = limit
        return self._call_tool("pdooh_search_local_community", arguments)

    def audience_insight(
        self,
        community_id: str,
    ) -> Dict[str, Any]:
        """AI 人群洞察。

        本地数据库工具 4/4：使用 AI 分析指定社区的人群洞察。

        Args:
            community_id: 社区 ID。

        Returns:
            AI 生成的人群洞察报告。
        """
        arguments = {"community_id": community_id}
        return self._call_tool("pdooh_audience_insight", arguments)

    # ==================== 1.3 点位查询工具 ====================

    def query_access_points(
        self,
        city: Optional[str] = None,
        district: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """查询门禁点位。

        点位查询工具 1/7：查询门禁广告点位。

        Args:
            city: 城市名称。
            district: 区名称。
            limit: 返回记录数量限制，默认 20。
            offset: 偏移量，默认 0。

        Returns:
            门禁点位列表。
        """
        arguments = build_query_params(
            city=city,
            district=district,
            limit=limit,
            offset=offset,
        )
        return self._call_tool("pdooh_query_access_points", arguments)

    def query_smart_frames(
        self,
        city: Optional[str] = None,
        district: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """查询单元门点位。

        点位查询工具 2/7：查询单元门智能屏点位。

        Args:
            city: 城市名称。
            district: 区名称。
            limit: 返回记录数量限制，默认 20。
            offset: 偏移量，默认 0。

        Returns:
            单元门点位列表。
        """
        arguments = build_query_params(
            city=city,
            district=district,
            limit=limit,
            offset=offset,
        )
        return self._call_tool("pdooh_query_smart_frames", arguments)

    def query_daocha_points(
        self,
        city: Optional[str] = None,
        district: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """查询道闸点位。

        点位查询工具 3/7：查询道闸广告点位。

        Args:
            city: 城市名称。
            district: 区名称。
            limit: 返回记录数量限制，默认 20。
            offset: 偏移量，默认 0。

        Returns:
            道闸点位列表。
        """
        arguments = build_query_params(
            city=city,
            district=district,
            limit=limit,
            offset=offset,
        )
        return self._call_tool("pdooh_query_daocha_points", arguments)

    def query_led_points(
        self,
        city: Optional[str] = None,
        district: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """查询 LED 点位。

        点位查询工具 4/7：查询 LED 广告屏点位。

        Args:
            city: 城市名称。
            district: 区名称。
            limit: 返回记录数量限制，默认 20。
            offset: 偏移量，默认 0。

        Returns:
            LED 点位列表。
        """
        arguments = build_query_params(
            city=city,
            district=district,
            limit=limit,
            offset=offset,
        )
        return self._call_tool("pdooh_query_led_points", arguments)

    def query_elevator_frames(
        self,
        city: Optional[str] = None,
        district: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """查询电梯框架。

        点位查询工具 5/7：查询电梯框架广告点位。

        Args:
            city: 城市名称。
            district: 区名称。
            limit: 返回记录数量限制，默认 20。
            offset: 偏移量，默认 0。

        Returns:
            电梯框架点位列表。
        """
        arguments = build_query_params(
            city=city,
            district=district,
            limit=limit,
            offset=offset,
        )
        return self._call_tool("pdooh_query_elevator_frames", arguments)

    def query_smart_screen_2025(
        self,
        city: Optional[str] = None,
        district: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """查询智能屏 2025 数据。

        点位查询工具 6/7：查询 2025 年智能屏数据。

        Args:
            city: 城市名称。
            district: 区名称。
            limit: 返回记录数量限制，默认 20。
            offset: 偏移量，默认 0。

        Returns:
            智能屏 2025 数据列表。
        """
        arguments = build_query_params(
            city=city,
            district=district,
            limit=limit,
            offset=offset,
        )
        return self._call_tool("pdooh_query_smart_screen_2025", arguments)

    def query_shadow_points(
        self,
        city: Optional[str] = None,
        district: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """查询投影屏点位。

        点位查询工具 7/7：查询投影屏（Shadow）广告点位。

        Args:
            city: 城市名称。
            district: 区名称。
            limit: 返回记录数量限制，默认 20。
            offset: 偏移量，默认 0。

        Returns:
            投影屏点位列表。
        """
        arguments = build_query_params(
            city=city,
            district=district,
            limit=limit,
            offset=offset,
        )
        return self._call_tool("pdooh_query_shadow_points", arguments)

    # ==================== 1.4 资源统计工具 ====================

    def query_city_resources(
        self,
        city: str,
    ) -> Dict[str, Any]:
        """查询城市资源统计。

        资源统计工具 1/3：查询指定城市的资源统计数据。

        Args:
            city: 城市名称。

        Returns:
            城市资源统计，包含各类型点位数量。
        """
        arguments = {"city": city}
        return self._call_tool("pdooh_query_city_resources", arguments)

    def query_city_summary(
        self,
    ) -> Dict[str, Any]:
        """查询全国城市汇总。

        资源统计工具 2/3：查询全国所有城市的资源汇总数据。

        Returns:
            全国城市资源汇总数据。
        """
        arguments: Dict[str, Any] = {}
        return self._call_tool("pdooh_query_city_summary", arguments)

    def query_customers(
        self,
        customer_id: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """查询客户资料。

        资源统计工具 3/3：查询客户资料信息。

        Args:
            customer_id: 客户 ID，指定时返回详情。
            limit: 返回记录数量限制，默认 20。
            offset: 偏移量，默认 0。

        Returns:
            客户资料列表或详情。
        """
        arguments = build_query_params(
            customer_id=customer_id,
            limit=limit,
            offset=offset,
        )
        return self._call_tool("pdooh_query_customers", arguments)

    # ==================== 1.5 ROI 计算工具 ====================

    def calc_roi(
        self,
        frames: int,
        period_weeks: int,
        category: str,
        media_type: str,
        price_type: str,
        city: Optional[str] = None,
        product: Optional[str] = None,
    ) -> Dict[str, Any]:
        """计算社区营销 ROI。

        ROI 计算工具 1/1：计算社区营销投资的 ROI。

        Args:
            frames: 屏幕数量（帧）。
            period_weeks: 投放周期（周）。
            category: 品类，如 "日化用品"。
            media_type: 媒体类型，如 "unit_door"、"dao_cha"、"led"。
            price_type: 价格类型，如 "exchange"（兑换价）、"retail"（零售价）。
            city: 城市名称，可选。
            product: 产品名称，可选。

        Returns:
            ROI 计算结果，包含 ROI 值、盈亏平衡点等。
        """
        arguments: Dict[str, Any] = {
            "frames": frames,
            "period_weeks": period_weeks,
            "category": category,
            "media_type": media_type,
            "price_type": price_type,
        }
        if city:
            arguments["city"] = city
        if product:
            arguments["product"] = product
        return self._call_tool("pdooh_calc_roi", arguments)

    def close(self) -> None:
        """关闭 HTTP 客户端连接。"""
        self.client.close()

    def __enter__(self) -> "MCPClient":
        """上下文管理器入口。"""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """上下文管理器退出。"""
        self.close()
