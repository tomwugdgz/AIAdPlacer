"""青柠 Booking P0 — 超卖防护压测门禁（T9 / CT-01~CT-06）。

依赖：PG(ai_adplacer) 在线、Redis 在线、ETL 已跑（media_resources 有数据）。
所有测试数据以 created_by='pytest_ct' 标记，测试结束时统一清理（ORM + 直插两路）。

CT-01 百并发同点位仅 1 成功
CT-02 锁位到期 cron 释放
CT-03 幂等键去重
CT-04 绕过应用层直插重叠触发 23P01（最后防线）
CT-05 冲突不产生脏数据
CT-06 多独立点位并发全成功（无交叉污染）

注：模块级 async_engine 绑定事件循环，所有异步调用经共享持久 loop（_run）。
"""
from __future__ import annotations

import asyncio
import uuid
from datetime import date, datetime, timedelta, timezone

import psycopg2
from sqlalchemy import delete, select

import app.core.async_db as _ad
from app.config import settings
from app.core.exceptions import QinglinError
from app.models import MediaResource
from app.models.booking import Booking, BookingStatus
from app.services.booking_service import create_booking
from app.tasks.booking_release import release_expired_bookings

PG_DSN = settings.DATABASE_URL
TEST_MARKER = "pytest_ct"


def _run(coro):
    loop = getattr(_ad, "_TEST_LOOP", None)
    if loop is None or loop.is_closed():
        loop = asyncio.new_event_loop()
        _ad._TEST_LOOP = loop
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


def pytest_sessionfinish(session):
    """释放共享 loop 与引擎连接，避免资源泄漏告警。"""
    loop = getattr(_ad, "_TEST_LOOP", None)
    if loop is not None and not loop.is_closed():
        try:
            loop.run_until_complete(_ad.async_engine.dispose())
        except Exception:
            pass
        loop.close()
        _ad._TEST_LOOP = None


# ── 工具 ──────────────────────────────────────────────────────────────
def _fetch_media_ids(n: int):
    async def _go():
        async with _ad.AsyncSessionLocal() as db:
            rows = (
                await db.execute(
                    select(MediaResource.id)
                    .where(MediaResource.source_table.isnot(None))
                    .limit(n)
                )
            ).scalars().all()
            return list(rows)

    return _run(_go())


def _cleanup():
    """清理 ORM 与 psycopg2 直插两类测试数据。"""
    async def _orm():
        async with _ad.AsyncSessionLocal() as db:
            await db.execute(delete(Booking).where(Booking.created_by == TEST_MARKER))
            await db.commit()

    _run(_orm())
    try:
        conn = psycopg2.connect(PG_DSN, connect_timeout=5)
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute("DELETE FROM bookings WHERE created_by = %s", (TEST_MARKER,))
        conn.close()
    except Exception:
        pass


async def _call_create(mid, d0, d1, key):
    async with _ad.AsyncSessionLocal() as db:
        return await create_booking(
            db, media_resource_id=mid, lock_start=d0, lock_end=d1,
            idempotency_key=key, created_by=TEST_MARKER,
        )


# ── CT-01 百并发同点位仅 1 成功 ───────────────────────────────────────
def test_ct01_concurrent_same_point_only_one():
    mids = _fetch_media_ids(1)
    assert mids, "需要至少 1 个 media_resource"
    mid = mids[0]
    d0, d1 = date(2026, 9, 1), date(2026, 9, 10)
    N = 30  # 总量模拟并发；信号量限制在连接池上限内避免连接耗尽误判
    sem = asyncio.Semaphore(8)

    async def _attempt():
        async with sem:
            async with _ad.AsyncSessionLocal() as db:
                try:
                    await create_booking(
                        db, media_resource_id=mid, lock_start=d0, lock_end=d1,
                        idempotency_key=f"ct01-{uuid.uuid4()}", created_by=TEST_MARKER,
                    )
                    return True
                except QinglinError:
                    return False

    try:
        results = _run(asyncio.gather(*[_attempt() for _ in range(N)]))
        successes = sum(results)
        assert successes == 1, f"期望仅 1 成功，实际 {successes}（超卖防护失效）"
    finally:
        _cleanup()


# ── CT-02 锁位到期 cron 释放 ──────────────────────────────────────────
def test_ct02_expiry_release():
    mids = _fetch_media_ids(1)
    assert mids
    mid = mids[0]

    async def _seed():
        async with _ad.AsyncSessionLocal() as db:
            past = datetime.now(timezone.utc) - timedelta(days=1)
            b = Booking(
                id=uuid.uuid4(), booking_no=f"BK-TEST-{uuid.uuid4().hex[:8]}",
                media_resource_id=mid, lock_tier="C",
                lock_start=date(2026, 9, 1), lock_end=date(2026, 9, 10),
                expire_at=past, status=BookingStatus.LOCKED,
                idempotency_key=f"ct02-{uuid.uuid4()}", created_by=TEST_MARKER,
                install_status="PENDING", extend_count=0,
            )
            db.add(b)
            await db.commit()

    try:
        _run(_seed())
        released = _run(release_expired_bookings())
        assert released >= 1, "应至少释放 1 条过期单"
        async def _check():
            async with _ad.AsyncSessionLocal() as db:
                rows = (
                    await db.execute(select(Booking).where(Booking.created_by == TEST_MARKER))
                ).scalars().all()
                return [b.status for b in rows]
        statuses = _run(_check())
        assert all(s == "EXPIRED" for s in statuses), statuses
    finally:
        _cleanup()


# ── CT-03 幂等键去重 ──────────────────────────────────────────────────
def test_ct03_idempotency():
    mids = _fetch_media_ids(1)
    mid = mids[0]
    key = f"ct03-{uuid.uuid4()}"
    d0, d1 = date(2026, 10, 1), date(2026, 10, 10)
    try:
        b1 = _run(_call_create(mid, d0, d1, key))
        b2 = _run(_call_create(mid, d0, d1, key))
        assert b1.id == b2.id, "相同幂等键应返回既有单（CT-03 失败）"
    finally:
        _cleanup()


# ── CT-04 绕过应用层直插重叠触发 23P01 ────────────────────────────────
def test_ct04_exclusion_23p01():
    mids = _fetch_media_ids(1)
    mid = mids[0]
    conn = psycopg2.connect(PG_DSN, connect_timeout=5)
    conn.autocommit = False
    cur = conn.cursor()
    try:
        cur.execute(
            """INSERT INTO bookings
               (id,booking_no,media_resource_id,lock_tier,lock_start,lock_end,expire_at,status,
                idempotency_key,install_status,extend_count,created_by,created_at,updated_at)
               VALUES (%s,%s,%s,'C','2026-11-01','2026-11-10',now(),'LOCKED',%s,'PENDING',0,%s,now(),now())""",
            (str(uuid.uuid4()), f"BK-{uuid.uuid4().hex[:8]}", str(mid),
             f"ct04a-{uuid.uuid4()}", TEST_MARKER),
        )
        conn.commit()
        cur.execute(
            """INSERT INTO bookings
               (id,booking_no,media_resource_id,lock_tier,lock_start,lock_end,expire_at,status,
                idempotency_key,install_status,extend_count,created_by,created_at,updated_at)
               VALUES (%s,%s,%s,'C','2026-11-05','2026-11-15',now(),'LOCKED',%s,'PENDING',0,%s,now(),now())""",
            (str(uuid.uuid4()), f"BK-{uuid.uuid4().hex[:8]}", str(mid),
             f"ct04b-{uuid.uuid4()}", TEST_MARKER),
        )
        conn.commit()
        raise AssertionError("期望 23P01 排他冲突，但未触发（最后防线失效）")
    except psycopg2.errors.ExclusionViolation:
        conn.rollback()
    finally:
        conn.rollback()
        cur.execute("DELETE FROM bookings WHERE created_by=%s", (TEST_MARKER,))
        conn.commit()
        conn.close()


# ── CT-05 冲突不产生脏数据 ────────────────────────────────────────────
def test_ct05_no_dirty_on_conflict():
    mids = _fetch_media_ids(1)
    mid = mids[0]
    d0, d1 = date(2026, 12, 1), date(2026, 12, 10)
    try:
        _run(_call_create(mid, d0, d1, f"ct05a-{uuid.uuid4()}"))

        async def _fail():
            async with _ad.AsyncSessionLocal() as db:
                try:
                    await create_booking(
                        db, media_resource_id=mid, lock_start=d0, lock_end=d1,
                        idempotency_key=f"ct05b-{uuid.uuid4()}", created_by=TEST_MARKER,
                    )
                    return False
                except QinglinError:
                    return True

        assert _run(_fail()) is True, "重叠锁位应被拦截"
        async def _count():
            async with _ad.AsyncSessionLocal() as db:
                return len(
                    (await db.execute(
                        select(Booking).where(
                            Booking.media_resource_id == mid,
                            Booking.lock_start == d0, Booking.lock_end == d1,
                        )
                    )).scalars().all()
                )
        assert _run(_count()) == 1, "冲突后应无脏数据（仅 1 条）"
    finally:
        _cleanup()


# ── CT-06 多独立点位并发全成功（无交叉污染）────────────────────────────
def test_ct06_distinct_points_all_success():
    mids = _fetch_media_ids(20)
    assert len(mids) >= 20, f"需要至少 20 个 media_resource，实际 {len(mids)}"
    base = date(2027, 1, 1)
    sem = asyncio.Semaphore(8)

    async def _attempt(i):
        mid = mids[i]
        d0 = base + timedelta(days=i)
        d1 = d0 + timedelta(days=10)
        async with sem:
            async with _ad.AsyncSessionLocal() as db:
                try:
                    await create_booking(
                        db, media_resource_id=mid, lock_start=d0, lock_end=d1,
                        idempotency_key=f"ct06-{uuid.uuid4()}", created_by=TEST_MARKER,
                    )
                    return True
                except QinglinError:
                    return False

    try:
        results = _run(asyncio.gather(*[_attempt(i) for i in range(20)]))
        assert sum(results) == 20, f"20 个独立点位应全成功，实际 {sum(results)}"
    finally:
        _cleanup()
