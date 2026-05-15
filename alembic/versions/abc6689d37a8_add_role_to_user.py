"""add_role_to_user

Revision ID: abc6689d37a8
Revises:
Create Date: 2026-05-08
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'abc6689d37a8'
down_revision: Union[str, Sequence[str], None] = '95022356c676'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Upgrade schema."""

    op.execute("""
        ALTER TABLE public."user"
        ADD COLUMN role VARCHAR(20) DEFAULT 'USER' NOT NULL;
    """)

def downgrade() -> None:
    """Downgrade schema."""

    op.execute("""
        ALTER TABLE public."user"
        DROP COLUMN ROLE
    """)