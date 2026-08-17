"""P0 初版迁移 — 青柠 Booking 真实锁位模块

修订内容（对应设计文档 §5 / P0-1~P0-3）：
1. 启用 btree_gist 扩展（排他约束前提）
2. media_resources 补全派生字段（level/city/area/project/point_no/source_table/dedup_key/media_type_code）
3. 创建枚举 booking_status / install_status / lock_tier
4. 创建 bookings 主表 + 档期 EXCLUDE 排他约束（防超卖最后防线）
5. 创建 lock_tier_config（五档参数）+ 种子
6. 创建 media_level_rule（level 派生配置）+ 种子

注意：本迁移为**权威 DDL 来源**。存量同步 ``init_db()``（create_all）即便先运行，
也只会创建缺表、不会破坏本迁移建立的 EXCLUDE 约束与种子；本迁移对已存在对象均用
``IF NOT EXISTS`` / ``ON CONFLICT`` / ``EXCEPTION WHEN duplicate_object`` 幂等。

若执行 ``CREATE EXTENSION IF NOT EXISTS btree_gist`` 报 permission denied，请立即停止
并向主理人报告——切勿绕过排他约束（不得删除 EXCLUDE / 不得改设计）。
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ① 扩展（排他约束前提）
    op.execute(sa.text("CREATE EXTENSION IF NOT EXISTS btree_gist"))

    # ② media_resources 补全派生字段（ETL 写入）
    op.execute(sa.text(
        """
        ALTER TABLE media_resources
          ADD COLUMN IF NOT EXISTS level            VARCHAR(4),
          ADD COLUMN IF NOT EXISTS city             VARCHAR(64),
          ADD COLUMN IF NOT EXISTS area             VARCHAR(64),
          ADD COLUMN IF NOT EXISTS project          VARCHAR(128),
          ADD COLUMN IF NOT EXISTS point_no         VARCHAR(64),
          ADD COLUMN IF NOT EXISTS source_table     VARCHAR(64),
          ADD COLUMN IF NOT EXISTS dedup_key        VARCHAR(128),
          ADD COLUMN IF NOT EXISTS media_type_code  VARCHAR(32)
        """
    ))
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_media_resources_dedup ON media_resources(dedup_key)"))
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_media_resources_level ON media_resources(level)"))
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_media_resources_mtype ON media_resources(media_type_code)"))

    # ③ 枚举
    op.execute(sa.text(
        "DO $$ BEGIN CREATE TYPE booking_status AS ENUM "
        "('SELECTED','LOCKED','PUBLISHED','RELEASED','EXPIRED','CANCELLED','TERMINATED'); "
        "EXCEPTION WHEN duplicate_object THEN NULL; END $$;"
    ))
    op.execute(sa.text(
        "DO $$ BEGIN CREATE TYPE install_status AS ENUM "
        "('PENDING','INSTALLED','VERIFIED','ABNORMAL'); "
        "EXCEPTION WHEN duplicate_object THEN NULL; END $$;"
    ))
    op.execute(sa.text(
        "DO $$ BEGIN CREATE TYPE lock_tier AS ENUM ('A++','A+','A','B','C'); "
        "EXCEPTION WHEN duplicate_object THEN NULL; END $$;"
    ))

    # ④ bookings 主表
    op.execute(sa.text(
        """
        CREATE TABLE IF NOT EXISTS bookings (
          id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          booking_no          VARCHAR(32) NOT NULL UNIQUE,
          media_resource_id   UUID NOT NULL REFERENCES media_resources(id),
          campaign_id         UUID REFERENCES campaigns(id),
          customer_id         VARCHAR(64),
          lock_tier           lock_tier NOT NULL,
          lock_start          DATE NOT NULL,
          lock_end            DATE NOT NULL,
          expire_at           TIMESTAMPTZ NOT NULL,
          status              booking_status NOT NULL DEFAULT 'SELECTED',
          idempotency_key     VARCHAR(128) NOT NULL UNIQUE,
          unit_price_snapshot NUMERIC(10,2),
          weeks               INTEGER,
          discount_rate       NUMERIC(5,4),
          extra_fee           NUMERIC(10,2),
          final_amount        NUMERIC(12,2),
          install_status      install_status NOT NULL DEFAULT 'PENDING',
          extend_count        INTEGER NOT NULL DEFAULT 0,
          cancel_reason       TEXT,
          created_by          VARCHAR(64),
          created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
          updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
          CONSTRAINT ck_booking_date_order CHECK (lock_end >= lock_start)
        )
        """
    ))

    # ⑤ 档期排他约束（核心）：同点位 LOCKED/PUBLISHED 区间重叠即拒（最后防线）
    op.execute(sa.text("ALTER TABLE bookings DROP CONSTRAINT IF EXISTS booking_no_overlap"))
    op.execute(sa.text(
        """
        ALTER TABLE bookings ADD CONSTRAINT booking_no_overlap
          EXCLUDE USING gist (
            media_resource_id WITH =,
            daterange(lock_start, lock_end, '[]') WITH &&
          ) WHERE (status IN ('LOCKED','PUBLISHED'))
        """
    ))

    # ⑥ 索引
    op.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS ix_bookings_media_status ON bookings(media_resource_id, status)"
    ))
    op.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS ix_bookings_expire ON bookings(expire_at) WHERE status = 'LOCKED'"
    ))
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_bookings_idem ON bookings(idempotency_key)"))

    # ⑦ 五档参数表 + 种子
    op.execute(sa.text(
        """
        CREATE TABLE IF NOT EXISTS lock_tier_config (
          level        lock_tier PRIMARY KEY,
          base_days    INTEGER NOT NULL,
          extend_times INTEGER NOT NULL,
          extend_days  INTEGER NOT NULL
        )
        """
    ))
    op.execute(sa.text(
        """
        INSERT INTO lock_tier_config(level, base_days, extend_times, extend_days) VALUES
          ('A++', 10, 1, 5), ('A+', 7, 1, 3), ('A', 7, 1, 3), ('B', 3, 1, 2), ('C', 3, 0, 0)
        ON CONFLICT (level) DO NOTHING
        """
    ))

    # ⑧ level 派生配置表 + 种子（P0 决策①默认规则）
    op.execute(sa.text(
        """
        CREATE TABLE IF NOT EXISTS media_level_rule (
          id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          match_type VARCHAR(12) NOT NULL,
          match_key  VARCHAR(64) NOT NULL,
          level      lock_tier  NOT NULL,
          priority   INTEGER NOT NULL DEFAULT 0,
          enabled    BOOLEAN NOT NULL DEFAULT true
        )
        """
    ))
    op.execute(sa.text(
        """
        INSERT INTO media_level_rule(match_type, match_key, level, priority) VALUES
          ('media_type','door_access',          'A+', 0),
          ('media_type','mall_led',             'A++',0),
          ('media_type','smart_screen_l9',      'A',  0),
          ('media_type','smart_screen_202507',  'A',  0),
          ('media_type','unit_door',            'B',  0),
          ('media_type','boom_gate',            'C',  0)
        ON CONFLICT DO NOTHING
        """
    ))
    op.execute(sa.text(
        """
        INSERT INTO media_level_rule(match_type, match_key, level, priority) VALUES
          ('city','广州天河',  'A++', 10),
          ('city','广州珠江新城','A++',10),
          ('city','北京朝阳',  'A++', 10),
          ('city','上海浦东',  'A++', 10)
        ON CONFLICT DO NOTHING
        """
    ))


def downgrade() -> None:
    op.execute(sa.text("ALTER TABLE bookings DROP CONSTRAINT IF EXISTS booking_no_overlap"))
    op.execute(sa.text("DROP TABLE IF EXISTS bookings"))
    op.execute(sa.text("DROP TABLE IF EXISTS lock_tier_config"))
    op.execute(sa.text("DROP TABLE IF EXISTS media_level_rule"))
    op.execute(sa.text("DROP TYPE IF EXISTS booking_status"))
    op.execute(sa.text("DROP TYPE IF EXISTS install_status"))
    op.execute(sa.text("DROP TYPE IF EXISTS lock_tier"))
