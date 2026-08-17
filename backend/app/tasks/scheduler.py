"""青柠 Booking — 定时释放调度器（设计文档 §10 / P0-6）。

优先使用 APScheduler（AsyncIOScheduler，新增轻依赖）；若 APScheduler 不可用，
回退为 asyncio 后台循环（main.py startup 中 ``asyncio.create_task`` 启动），
两种方案调用同一 ``release_expired_bookings()``，均满足 P0-6。
"""
from __future__ import annotations

import asyncio
import logging

from app.config import settings
from app.tasks.booking_release import release_expired_bookings

logger = logging.getLogger("qinglin_scheduler")

_HAS_APS = False
try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler

    _HAS_APS = True
except Exception:  # noqa: BLE001
    AsyncIOScheduler = None  # type: ignore

_scheduler = None


async def ensure_release_scheduler_started() -> str:
    """启动到期释放调度。返回所用方案：'apscheduler' 或 'asyncio_loop'。"""
    global _scheduler
    if _HAS_APS:
        if _scheduler is None or not _scheduler.running:
            _scheduler = AsyncIOScheduler()
            _scheduler.add_job(
                release_expired_bookings,
                "interval",
                seconds=settings.BOOKING_RELEASE_CRON_SECONDS,
                id="release_expired_bookings",
                replace_existing=True,
                max_instances=1,
            )
            _scheduler.start()
        return "apscheduler"
    else:
        # 回退：asyncio 后台循环
        loop = asyncio.get_event_loop()
        loop.create_task(_release_loop())
        return "asyncio_loop"


async def _release_loop() -> None:
    """APScheduler 不可用时的兜底循环：每 N 秒扫描一次。"""
    logger.warning("APScheduler 不可用，使用 asyncio 循环作为到期释放兜底")
    while True:
        try:
            await release_expired_bookings()
        except Exception as e:  # noqa: BLE001
            logger.warning("到期释放执行异常: %s", e)
        await asyncio.sleep(settings.BOOKING_RELEASE_CRON_SECONDS)


def shutdown_release_scheduler() -> None:
    global _scheduler
    if _scheduler is not None and getattr(_scheduler, "running", False):
        _scheduler.shutdown(wait=False)
        _scheduler = None
