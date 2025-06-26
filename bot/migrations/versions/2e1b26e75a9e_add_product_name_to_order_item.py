from alembic import op
import sqlalchemy as sa

revision: str = "2e1b26e75a9e"
down_revision: str | None = "4e09e7f3c4f2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. добавляем колонку сразу с server_default = ''
    #    → postgres проставит пустую строку во все существующие записи
    op.add_column(
        "order_item",
        sa.Column(
            "product_name",
            sa.String(length=150),
            nullable=False,
            server_default="",      # <--- ключевая строчка
        ),
    )

    # 2. если нужно – убираем default, чтобы дальше он не ставился автоматически
    op.alter_column("order_item", "product_name", server_default=None)

    # 3. создаём индекс (необязательно – уберите, если уже есть)
    op.create_index(
        "idx_order_item_order",
        "order_item",
        ["order_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_order_item_order", table_name="order_item")
    op.drop_column("order_item", "product_name")
