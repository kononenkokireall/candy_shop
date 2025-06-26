"""fill username + set not null

Revision ID: 4e09e7f3c4f2
Revises: 059f25884521
Create Date: 2025-06-22 15:16:27.652170

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '4e09e7f3c4f2'
down_revision: Union[str, None] = '059f25884521'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # если колонки вдруг нет (другая БД) — добавим
    op.execute(
        'ALTER TABLE "user" ADD COLUMN IF NOT EXISTS username VARCHAR(64)')

    # заполняем NULL-ы
    op.execute("""
        UPDATE "user"
        SET username = COALESCE(username, first_name, '')
    """)

    # делаем NOT NULL (если нужно)
    op.alter_column("user", "username", nullable=False)
