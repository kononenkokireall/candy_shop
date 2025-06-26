"""add username to user

Revision ID: 059f25884521
Revises: e37eca1e968c
Create Date: 2025-06-22 15:04:24.487010

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '059f25884521'
down_revision: Union[str, None] = 'e37eca1e968c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. добавляем колонку, но nullable=True
    op.add_column(
        "user",
        sa.Column("username", sa.String(length=64), nullable=True)
    )

    # 2. (по желанию) заполняем существующие строки
    #    здесь ставим пустую строку или first_name как fallback
    op.execute("""
        UPDATE "user"
        SET username = COALESCE(username, first_name, '')
    """)

    # 3. ↓ если хотите NOT NULL – делаем ТОЛЬКО после заполнения
    # op.alter_column("user", "username", nullable=False)


def downgrade() -> None:
    op.drop_column("user", "username")
