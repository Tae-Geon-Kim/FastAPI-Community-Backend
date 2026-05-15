"""

Revision ID: fcaa8c1883c3
Revises: e69ce12dcaea
Create Date: 2026-05-12 

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'fcaa8c1883c3'
down_revision: Union[str, Sequence[str], None] = 'e69ce12dcaea'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Upgrade Schema."""
    op.alter_column("user", "ban_util", new_column_name = "ban_end_at")


def downgrade() -> None:
    """Downgrade Schema."""
    op.alter_column("user", "ban_end_at", new_column_name = "ban_util")
