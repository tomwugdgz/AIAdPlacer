"""
智能屏资源子系统（Smart Screen L9）— roi_estimate 真实 ROI 模型单测。

纯函数测试：直接 import indicator_formulas.roi_estimate，构造小区级宽表 dict，
不依赖数据库。验证「成本=CPM×日触达/1000、收益=日触达×CVR×AOV、
真实 ROI=(收益-成本)/成本、映射 0–100 指数」的可解释模型。

作者: 寇豆码（Kou）
日期: 2026-06-20
"""

import pytest

from app.smart_screen.indicator_formulas import roi_estimate, CVR, AOV


# ── 用例 1：中值用例（验证非饱和）──────────────────────────────────────────────
def test_roi_estimate_mid_value():
    # daily_reach = 100 * 1.0 * 2.1 = 210；access_lightbox_price=80 → cost=80
    # revenue = 210 * 0.008 * 80 = 134.4；roi = (134.4-80)/80 = 0.68
    # 指数 = 0.68*50 + 50 = 84.0
    row = {
        "household_count": 100,
        "occupancy_rate": 1.0,
        "access_lightbox_price": 80,
    }
    assert roi_estimate(row) == pytest.approx(84.0)


# ── 用例 2：饱和用例（ROI ≥ 100% → 指数封顶 100.0）────────────────────────────
def test_roi_estimate_saturated():
    # 极大触达 → 收益远大于成本 → ROI≥100% → 指数=100.0
    row = {
        "household_count": 10_000_000,
        "occupancy_rate": 1.0,
        "access_lightbox_price": 80,
    }
    assert roi_estimate(row) == pytest.approx(100.0)


# ── 用例 3：触达极小 / 成本极高（ROI ≤ −100% → 指数触底 0.0）──────────────────
def test_roi_estimate_loss_floor():
    # 触达极小（reach 钳制为 1.0）+ 成本极高（access_lightbox_price=1e6）
    # → ROI≈-100% → 指数=0.0
    row = {
        "household_count": 0,
        "occupancy_rate": 0.0,
        "access_lightbox_price": 1_000_000,
    }
    assert roi_estimate(row) == pytest.approx(0.0)


# ── 用例 4：指数始终落在 0–100 闭区间（边界健壮性）────────────────────────────
def test_roi_estimate_bounds():
    rows = [
        {"household_count": 0, "occupancy_rate": 0.0, "access_lightbox_price": 0},
        {"household_count": 1, "occupancy_rate": 0.5, "access_lightbox_price": 5000},
        {"household_count": 500, "occupancy_rate": 0.9, "access_lightbox_price": 120},
        {"household_count": 5000, "occupancy_rate": 1.0, "access_lightbox_price": 60},
    ]
    for row in rows:
        v = roi_estimate(row)
        assert 0.0 <= v <= 100.0


# ── 用例 5：常量口径校验（单一事实来源，避免回归被改）─────────────────────────
def test_roi_constants():
    # 社区梯媒统一假设常量，来源见 indicator_formulas 模块注释
    assert CVR == pytest.approx(0.008)
    assert AOV == pytest.approx(80.0)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
