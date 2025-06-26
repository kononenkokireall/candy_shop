"""add product_name to order_item

Revision ID: 306fa6288156
Revises: ff8fc2a0860f
Create Date: 2025-06-18 10:39:55.646846

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '306fa6288156'
down_revision: Union[str, None] = 'ff8fc2a0860f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
