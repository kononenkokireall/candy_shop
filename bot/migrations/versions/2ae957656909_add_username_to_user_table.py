"""add username to user table

Revision ID: 2ae957656909
Revises: 306fa6288156
Create Date: 2025-06-22 14:46:34.263296

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2ae957656909'
down_revision: Union[str, None] = '306fa6288156'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
