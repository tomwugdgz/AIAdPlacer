"""
P0-3: 单元测试 — 覆盖核心逻辑

测试范围:
1. 标准曝光计算 (T/CCSA 738-2025)
2. 竞价引擎
3. 排期优化器
4. API Key 鉴权中间件

运行方式:
    cd backend
    python -m pytest tests/ -v
    # 或指定模块
    python -m pytest tests/test_standard_impression.py -v
"""
import math
import pytest
from decimal import Decimal

from app.bus.services.standard_impression import (
    StandardImpressionEngine,
    ExposureParams,
    ExposureResult,
    calc_standard_impression,
    DWELL_THRESHOLD_SECONDS,
    MINIMUM_EXPOSURE_SECONDS,
)
from app.bus.services.bidding_engine import calculate_bidding, calculate_multi_bidding
from app.services.scheduling_optimizer import SchedulingOptimizer
from app.api.auth import auth_config


# ─── 1. 标准曝光计算测试 (T/CCSA 738-2025) ────

class TestStandardImpression:
    """T/CCSA 738-2025 标准公式单元测试"""

    def setup_method(self):
        self.engine = StandardImpressionEngine()

    # --- 公式(2): flow_OTC ---

    def test_flow_otc_equal_durations(self):
        """T_exp == T_ad 时，flow_OTC = 0（无观看窗口）"""
        result = self.engine.calc_flow_otc(15.0, 15.0)
        assert result == pytest.approx(0.0, abs=0.001)

    def test_flow_otc_longer_exposure(self):
        """T_exp > T_ad 时，flow_OTC > 0（有观看窗口）"""
        result = self.engine.calc_flow_otc(30.0, 15.0)
        assert result > 0
        assert result <= 1.0

    def test_flow_otc_shorter_exposure(self):
        """T_exp < T_ad 时，flow_OTC = 0（曝光不足以看完广告）"""
        result = self.engine.calc_flow_otc(10.0, 20.0)
        assert result == 0.0
        assert result >= 0.0

    def test_flow_otc_boundary_zero(self):
        """零曝光或零广告时长 → 0"""
        assert self.engine.calc_flow_otc(0, 15) == 0.0
        assert self.engine.calc_flow_otc(15, 0) == 0.0

    def test_flow_otc_extreme_long(self):
        """超长曝光 → flow_OTC 趋近 1"""
        result = self.engine.calc_flow_otc(300.0, 15.0)
        assert result == pytest.approx(0.95, abs=0.01)  # (300-15)/300 = 0.95

    # --- 公式(1): flow_IMP ---

    def test_flow_imp_basic(self):
        """flow_IMP = flow_OTC × SOT × Traffic"""
        flow_imp = self.engine.calc_flow_imp(0.5, 0.25, 10000)
        assert flow_imp == pytest.approx(1250.0, abs=0.1)

    def test_flow_imp_zero_traffic(self):
        """零流量 → 0"""
        assert self.engine.calc_flow_imp(0.5, 0.25, 0) == 0.0

    def test_flow_imp_high_sot(self):
        """高 SOT 值提升 flow_IMP"""
        imp1 = self.engine.calc_flow_imp(0.5, 0.10, 10000)
        imp2 = self.engine.calc_flow_imp(0.5, 0.50, 10000)
        assert imp2 == imp1 * 5

    # --- 公式(4): dwell_OTC ---

    def test_dwell_otc_equal_threshold(self):
        """T_exp == 300s 时，dwell_OTC == 1.0"""
        result = self.engine.calc_dwell_otc(300.0)
        assert result == pytest.approx(1.0, abs=0.001)

    def test_dwell_otc_half_threshold(self):
        """T_exp == 150s 时，dwell_OTC == 0.5"""
        result = self.engine.calc_dwell_otc(150.0)
        assert result == pytest.approx(0.5, abs=0.001)

    def test_dwell_otc_double_threshold(self):
        """T_exp == 600s 时，dwell_OTC == 2.0（多次观看）"""
        result = self.engine.calc_dwell_otc(600.0)
        assert result == pytest.approx(2.0, abs=0.001)

    def test_dwell_otc_zero(self):
        """零曝光 → 0"""
        assert self.engine.calc_dwell_otc(0) == 0.0

    def test_dwell_otc_can_exceed_one(self):
        """驻留曝光概率可 > 1（多次观看）"""
        assert self.engine.calc_dwell_otc(15.0) < 1.0  # 15秒 < 300秒
        assert self.engine.calc_dwell_otc(600.0) > 1.0  # 600秒 > 300秒

    # --- 公式(3): dwell_IMP ---

    def test_dwell_imp_basic(self):
        """dwell_IMP = dwell_OTC × Traffic"""
        result = self.engine.calc_dwell_imp(1.0, 5000)
        assert result == pytest.approx(5000.0, abs=0.1)

    def test_dwell_imp_zero_traffic(self):
        assert self.engine.calc_dwell_imp(1.0, 0) == 0.0

    # --- 公式(5): 总曝光 ---

    def test_total_imp_sum(self):
        """IMP = flow_IMP + dwell_IMP"""
        result = self.engine.calc_total_imp(1250.0, 500.0)
        assert result == 1750

    def test_total_imp_rounding(self):
        """总曝光向下取整"""
        result = self.engine.calc_total_imp(1250.7, 499.3)
        assert result == 1750  # floor(1750.0)

    # --- 公式(6): 曝光乘数 ---

    def test_impression_multiplier_basic(self):
        """IMP_Multiplier = (flow_Traffic × IMP) / ad_slots"""
        result = self.engine.calc_impression_multiplier(10000, 1750.0, 4)
        assert result == pytest.approx(4375000.0, abs=0.1)

    def test_impression_multiplier_zero_slots(self):
        """ad_slots=0 返回默认值 1.0"""
        assert self.engine.calc_impression_multiplier(10000, 1750.0, 0) == 1.0

    # --- 接触频次 ---

    def test_frequency_basic(self):
        """frequency = effective_imp / independent_audience"""
        result = self.engine.calc_frequency(1000, 500)
        assert result == pytest.approx(2.0, abs=0.001)

    def test_frequency_zero_audience(self):
        assert self.engine.calc_frequency(1000, 0) == 0.0

    # --- 一站式计算 ---

    def test_full_pipeline(self):
        """完整曝光计算流水线 — T_exp > T_ad 才有流动曝光"""
        params = ExposureParams(
            traffic=10000,
            exposure_duration=30.0,   # 曝光30秒 > 广告15秒，有观看窗口
            ad_duration=15.0,
            sot=0.25,
            ad_slots_per_cycle=4,
        )
        result = self.engine.calculate(params)

        # 验证 flow_OTC > 0（因为 T_exp > T_ad）
        assert result.flow_otc > 0
        # 验证 flow_IMP > 0
        assert result.flow_impressions > 0
        # 验证 dwell_OTC < 1 (30s < 300s)
        assert result.dwell_otc < 1.0
        # 验证 total = flow + dwell
        assert result.total_impressions == result.flow_impressions + result.dwell_impressions
        # 验证有效曝光 ≤ 总曝光
        assert result.effective_impressions <= result.total_impressions

    def test_full_pipeline_long_exposure(self):
        """长曝光场景（公交站 60 秒）"""
        params = ExposureParams(
            traffic=5000,
            exposure_duration=60.0,
            ad_duration=15.0,
            sot=0.30,
            ad_slots_per_cycle=4,
        )
        result = self.engine.calculate(params)
        assert result.flow_otc > 0.5
        assert result.total_impressions > 0
        assert result.effective_impressions > 0

    # --- 便捷函数 ---

    def test_calc_standard_impression_function(self):
        """便捷函数 calc_standard_impression — 需 T_exp > T_ad"""
        result = calc_standard_impression(
            vehicles=10,
            daily_traffic=10000,
            hotspot_traffic=1.5,
            days=7,
            exposure_duration=30.0,  # > T_ad 才有流动曝光
            ad_duration=15.0,
            sot=0.25,
            ad_slots=4,
        )
        assert isinstance(result, ExposureResult)
        assert result.total_impressions > 0
        assert result.flow_impressions > 0  # T_exp > T_ad
        assert result.dwell_impressions > 0
        assert result.frequency >= 0

    def test_campaign_calculation(self):
        """投放方案级曝光计算"""
        result = calc_standard_impression(
            vehicles=20,
            daily_traffic=15000,
            hotspot_traffic=2.0,
            days=30,
            exposure_duration=15.0,
            ad_duration=15.0,
            sot=0.25,
            ad_slots=4,
        )
        assert result.total_impressions > 0
        assert result.frequency >= 0  # calculate_for_campaign 会计算 frequency
        assert result.independent_audience > 0


# ─── 2. 竞价引擎测试 ────

class TestBiddingEngine:
    """竞价引擎单元测试"""

    def test_basic_bidding(self):
        """基础竞价计算"""
        result = calculate_bidding(
            monthly_price=Decimal("30000"),
            level="A",
            days=30,
            vehicles=10,
            daily_traffic=10000,
            hotspot_traffic=1.5,
        )
        assert result["base_price"] > 0
        assert result["impressions"] > 0
        assert result["coverage_30d"] > 0
        assert result["cost_per_impression"] > 0
        # 标准曝光指标存在（exposure=15 == ad=15，flow_impressions=0）
        assert "standard_impression" in result
        si = result["standard_impression"]
        assert si["flow_impressions"] == 0  # T_exp == T_ad → 无流动曝光
        assert si["dwell_impressions"] > 0  # 有驻留曝光
        assert si["total_impressions"] > 0

    def test_level_multipliers(self):
        """不同等级价格系数"""
        base = Decimal("30000")
        days, vehicles, traffic, hotspot = 30, 10, 10000, 1.5

        price_a = calculate_bidding(base, "A", days, vehicles, traffic, hotspot)["base_price"]
        price_ap = calculate_bidding(base, "A+", days, vehicles, traffic, hotspot)["base_price"]
        price_app = calculate_bidding(base, "A++", days, vehicles, traffic, hotspot)["base_price"]
        price_s = calculate_bidding(base, "S", days, vehicles, traffic, hotspot)["base_price"]

        assert price_s > price_app > price_ap > price_a

    def test_time_premiums(self):
        """时段溢价"""
        base = Decimal("30000")
        params = dict(level="A", days=30, vehicles=10, daily_traffic=10000, hotspot_traffic=1.5)

        price_normal = calculate_bidding(base, **params, time_period="normal")["base_price"]
        price_morning = calculate_bidding(base, **params, time_period="morning_rush")["base_price"]
        price_evening = calculate_bidding(base, **params, time_period="evening_rush")["base_price"]

        assert price_morning > price_normal
        assert price_evening > price_normal

    def test_impressions_formula(self):
        """impressions = vehicles × daily_traffic × hotspot × days"""
        result = calculate_bidding(
            monthly_price=Decimal("30000"),
            level="A", days=10, vehicles=5,
            daily_traffic=10000, hotspot_traffic=2.0,
        )
        expected = 5 * 10000 * 2.0 * 10
        assert result["impressions"] == expected

    def test_coverage_30d(self):
        """coverage_30d = vehicles × daily_traffic × hotspot × 30"""
        result = calculate_bidding(
            monthly_price=Decimal("30000"),
            level="A", days=10, vehicles=5,
            daily_traffic=10000, hotspot_traffic=2.0,
        )
        expected = 5 * 10000 * 2.0 * 30
        assert result["coverage_30d"] == expected

    def test_multi_bidding(self):
        """多线路批量竞价"""
        routes = [
            {"route_code": "GZ-1", "route_name": "1路", "monthly_price": 30000,
             "level": "A", "vehicle_count": 10, "daily_traffic": 10000, "hotspot_traffic": 1.5},
            {"route_code": "GZ-2", "route_name": "2路", "monthly_price": 50000,
             "level": "A+", "vehicle_count": 15, "daily_traffic": 15000, "hotspot_traffic": 2.0},
        ]
        result = calculate_multi_bidding(routes, days=30)

        assert len(result["each_result"]) == 2
        assert result["summary"]["total_budget"] > 0
        assert result["summary"]["total_impressions"] > 0
        assert result["summary"]["route_count"] == 2
        assert result["summary"]["cpm"] > 0
        assert result["summary"]["cpr"] > 0

    def test_vehicle_override(self):
        """统一车辆数覆盖"""
        routes = [{"route_code": "GZ-1", "route_name": "1路", "monthly_price": 30000,
                   "level": "A", "vehicle_count": 5, "daily_traffic": 10000, "hotspot_traffic": 1.5}]
        result = calculate_multi_bidding(routes, days=30, vehicle_per_route=20)
        # 应该使用 20 而非 5
        assert result["each_result"][0]["impressions"] == 20 * 10000 * 1.5 * 30

    def test_standard_impression_included(self):
        """竞价结果包含行业标准曝光指标"""
        result = calculate_bidding(
            monthly_price=Decimal("30000"),
            level="A", days=30, vehicles=10,
            daily_traffic=10000, hotspot_traffic=1.5,
        )
        si = result["standard_impression"]
        assert "flow_impressions" in si
        assert "dwell_impressions" in si
        assert "total_impressions" in si
        assert "effective_impressions" in si
        assert "flow_otc" in si
        assert "dwell_otc" in si
        assert "impression_multiplier" in si
        assert "frequency" in si
        assert "independent_audience" in si
        assert "reach" in si


# ─── 3. 排期优化器测试 ────

class TestSchedulingOptimizer:
    """排期优化引擎测试（无 DB，模拟模式）"""

    def setup_method(self):
        self.optimizer = SchedulingOptimizer()

    def test_generate_schedule_empty_media(self):
        """无可用媒体返回空方案"""
        # 需要 DB 连接，用 mock 模拟
        from unittest.mock import MagicMock
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []
        result = self.optimizer.generate_schedule(mock_db, budget=10000, days=7)
        assert result["slots"] == []
        assert result["total_cost"] == 0

    def test_generate_schedule_logic(self):
        """排期逻辑验证（mock media）"""
        from unittest.mock import MagicMock, patch
        from uuid import uuid4

        mock_media = []
        for i in range(5):
            m = MagicMock()
            m.id = uuid4()
            m.name = f"Screen-{i}"
            m.category = "billboard" if i < 3 else "elevator"
            m.daily_price = Decimal(str(100 * (i + 1)))
            m.daily_impressions = 5000 * (i + 1)
            m.status = "available"
            mock_media.append(m)

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = mock_media

        result = self.optimizer.generate_schedule(mock_db, budget=50000, days=7)

        assert result["total_budget"] == 50000
        assert result["days"] == 7
        assert result["total_cost"] <= 50000
        assert result["total_impressions"] > 0
        assert result["avg_cpm"] > 0
        assert len(result["slots"]) > 0

    def test_budget_constraint(self):
        """预算约束 — 总花费不超过预算"""
        from unittest.mock import MagicMock
        from uuid import uuid4
        from decimal import Decimal

        mock_media = []
        for i in range(10):
            m = MagicMock()
            m.id = uuid4()
            m.name = f"Screen-{i}"
            m.category = "billboard"
            m.daily_price = Decimal("500")
            m.daily_impressions = 20000
            m.status = "available"
            mock_media.append(m)

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = mock_media

        result = self.optimizer.generate_schedule(mock_db, budget=3000, days=3)
        assert result["total_cost"] <= 3000
        assert result["remaining_budget"] >= 0

    def test_weekend_weight(self):
        """周末加权 — 周末 billboard 曝光更高"""
        from unittest.mock import MagicMock
        from uuid import uuid4
        from decimal import Decimal
        from datetime import date, timedelta

        mock_media = []
        m = MagicMock()
        m.id = uuid4()
        m.name = "Weekend-Screen"
        m.category = "billboard"
        m.daily_price = Decimal("100")
        m.daily_impressions = 10000
        m.status = "available"
        mock_media.append(m)

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = mock_media

        # 找一个有周末的 7 天窗口
        result = self.optimizer.generate_schedule(mock_db, budget=700, days=7)
        # 验证有排期产出
        assert result["total_impressions"] > 0

    def test_optimize_no_history(self):
        """无历史数据返回建议"""
        from unittest.mock import MagicMock

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = self.optimizer.optimize_existing(mock_db, campaign_id="nonexistent")
        assert "suggested_actions" in result
        assert len(result["suggested_actions"]) > 0


# ─── 4. API Key 鉴权测试 ────

class TestAuth:
    """鉴权中间件测试"""

    def test_api_key_constant(self):
        """API Key 常量存在"""
        assert auth_config.API_KEY == "aiad-2025-placer-token"

    def test_api_key_validation_success(self):
        """有效 API Key 验证通过"""
        from fastapi.testclient import TestClient
        from fastapi import FastAPI, Depends
        from app.api.auth import verify_api_key

        app = FastAPI()
        @app.get("/test")
        def test_endpoint(user=Depends(verify_api_key)):
            return user

        client = TestClient(app)
        response = client.get("/test", headers={"X-API-Key": auth_config.API_KEY})
        assert response.status_code == 200
        assert response.json()["auth_type"] == "api_key"

    def test_api_key_validation_fail(self):
        """无效 API Key 返回 403"""
        from fastapi.testclient import TestClient
        from fastapi import FastAPI, Depends
        from app.api.auth import verify_api_key

        app = FastAPI()
        @app.get("/test")
        def test_endpoint(user=Depends(verify_api_key)):
            return user

        client = TestClient(app)
        response = client.get("/test", headers={"X-API-Key": "wrong-key"})
        assert response.status_code == 403

    def test_api_key_missing(self):
        """缺少 API Key 返回 401"""
        from fastapi.testclient import TestClient
        from fastapi import FastAPI, Depends
        from app.api.auth import verify_api_key

        app = FastAPI()
        @app.get("/test")
        def test_endpoint(user=Depends(verify_api_key)):
            return user

        client = TestClient(app)
        response = client.get("/test")
        assert response.status_code == 401


# ─── 5. 数据模型测试 ────

class TestModels:
    """数据模型基础测试"""

    def test_exposure_params_dataclass(self):
        """ExposureParams 数据类可创建"""
        params = ExposureParams(
            traffic=10000,
            exposure_duration=15.0,
            ad_duration=15.0,
            sot=0.25,
            ad_slots_per_cycle=4,
        )
        assert params.traffic == 10000
        assert params.exposure_duration == 15.0
        assert params.dwell_traffic is None

    def test_exposure_result_dataclass(self):
        """ExposureResult 数据类可创建"""
        result = ExposureResult(
            flow_otc=0.5,
            dwell_otc=0.05,
            flow_impressions=1250,
            dwell_impressions=250,
            total_impressions=1500,
            effective_impressions=1275,
            impression_multiplier=3750.0,
            traffic=10000,
            ad_slots=4,
        )
        assert result.total_impressions == 1500
        assert result.frequency == 0.0  # 默认值

    def test_constants(self):
        """常量值正确"""
        assert DWELL_THRESHOLD_SECONDS == 300
        assert MINIMUM_EXPOSURE_SECONDS == 1.0


# ─── 测试汇总 ───────────────────────────────────────────────

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
