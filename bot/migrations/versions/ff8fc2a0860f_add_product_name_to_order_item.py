"""add product_name to order_item

Revision ID: ff8fc2a0860f
Revises:      f7e8ca818752
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# ──────────────────────────────────────────────────────────────────────────────
revision: str = "ff8fc2a0860f"
down_revision: Union[str, None] = "f7e8ca818752"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None
# ──────────────────────────────────────────────────────────────────────────────

# Enum-объект только для декларации
order_status = postgresql.ENUM(
    "PENDING",
    "PAID",
    "SHIPPED",
    "CANCELLED",
    "CONFIRMED",  # ← новое значение!
    name="order_status",
    create_type=False,  # Alembic не будет создавать тип автоматически
)


def upgrade() -> None:
    conn = op.get_bind()

    # ── 1.  Убедиться, что enum существует ───────────────────────────────────
    # (на проде он уже есть, а в fresh-DB — нет)
    with op.get_context().autocommit_block():
        conn.execute(
            sa.text(
                "DO $$ BEGIN "
                "  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'order_status') THEN "
                "    CREATE TYPE order_status AS ENUM ('PENDING','PAID','SHIPPED','CANCELLED'); "
                "  END IF; "
                "END$$;"
            )
        )

    # ── 2.  *Отдельная* транзакция для ADD VALUE  ────────────────────────────
    # Чтобы избежать ошибки «unsafe use of new value»
    with op.get_context().autocommit_block():
        conn.execute(
            sa.text(
                "ALTER TYPE order_status ADD VALUE IF NOT EXISTS 'CONFIRMED'")
        )

    # ── 3.  Правки схемы  ────────────────────────────────────────────────────
    # 3.1  product_name в order_item
    op.add_column(
        "order_item",
        sa.Column("product_name", sa.String(150), nullable=False,
                  server_default="")
    )
    op.alter_column("order_item", "product_name", server_default=None)
    op.create_index("idx_order_item_order", "order_item", ["order_id"])

    # 3.2  колонка status → enum
    # привести старые значения к CAPS (telegram хранит lower-case)
    op.execute("UPDATE orders SET status = UPPER(status)")

    op.execute(
        "ALTER TABLE orders "
        "ALTER COLUMN status TYPE order_status "
        "USING status::order_status"
    )

    # 3.3  housekeeping: больше не нужна category.created_at
    op.drop_column("category", "created_at")

    # 3.4  user.user_id — просто привести объявление к актуальному виду
    op.alter_column(
        "user",
        "user_id",
        existing_type=sa.BIGINT(),
        existing_nullable=False,
        autoincrement=True,
        existing_server_default=sa.text(
            "nextval('user_user_id_seq'::regclass)"),
    )


def downgrade() -> None:
    # обратные действия, БЕЗ удаления значения 'CONFIRMED'
    op.add_column(
        "category",
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    op.execute("ALTER TABLE orders ALTER COLUMN status TYPE VARCHAR(20)")
    op.drop_index("idx_order_item_order", table_name="order_item")
    op.drop_column("order_item", "product_name")

    # enum остаётся расширенным — убирать значение небезопасно
