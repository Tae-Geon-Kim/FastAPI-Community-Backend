"""add_deleted_by_to_boards

Revision ID: 742bceab28da
Revises: df637d83764c
Create Date: 2026-05-26 11:50:47.777193

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '742bceab28da'
down_revision: Union[str, Sequence[str], None] = 'df637d83764c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    
    op.execute("""
        ALTER TABLE public.boards
        ADD COLUMN deleted_by VARCHAR(20) DEFAULT NULL
    """)


def downgrade() -> None:
    """Downgrade schema."""

    op.execute("""
        ALTER TABLE public.boards
        DROP COLUMN deleted_by
    """)