from alembic import op
import sqlalchemy as sa

revision = "f31ce3d0cdb3"
down_revision = "2e1b26e75a9e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. добавляем колонку с временным server_default = '0'
    op.add_column(
        "product",
        sa.Column("stock", sa.Integer(), nullable=False, server_default="0")
    )
    # 2. убираем server_default, чтобы модель управляла значением
    op.alter_column("product", "stock", server_default=None)


def downgrade() -> None:
    op.drop_column("product", "stock")
