"""add_user_profile_fields

Revision ID: 7f84ed4e56e0
Revises: a2a59fbe5a70
Create Date: 2026-06-15 15:30:21.575397

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7f84ed4e56e0'
down_revision: Union[str, Sequence[str], None] = 'a2a59fbe5a70'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.execute("""
        ALTER TABLE public."user"
        ADD COLUMN name VARCHAR(50) NOT NULL
    """)

    op.execute("""
        ALTER TABLE public."user"
        ADD COLUMN email VARCHAR(100) NOT NULL
    """)

    op.execute("""
        ALTER TABLE public."user"
        ADD COLUMN is_verified BOOLEAN DEFAULT FALSE
    """)

def downgrade() -> None:
    """Downgrade schema."""

    op.execute("""
        ALTER TABLE public."user"
        DROP COLUMN is_verified  
    """)

    op.execute("""
        ALTER TABLE public."user"
        DROP COLUMN email
    """)

    op.execute("""
        ALTER TABLE public."user"
        DROP COLUMN name
    """)
