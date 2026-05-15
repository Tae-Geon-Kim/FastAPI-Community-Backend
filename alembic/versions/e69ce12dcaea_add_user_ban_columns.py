"""add_user_ban_columns

Revision ID: e69ce12dcaea
Revises: 8d22fa7ebe60
Create Date: 2026-05-12 

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'e69ce12dcaea'
down_revision: Union[str, Sequence[str], None] = '8d22fa7ebe60'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Upgrade Schema."""

    op.add_column(
        "user",
        sa.Column("ban_count", sa.Integer(), nullable = False, server_default = '0')
    )

    op.add_column(
        "user",
        sa.Column("ban_util", sa.DateTime(), nullable = True)
    )

def downgrade() -> None:
    """Downgrade Schema."""
    
    op.drop_column("user", "ban_util")

    op.drop_column("user", "ban_count")
