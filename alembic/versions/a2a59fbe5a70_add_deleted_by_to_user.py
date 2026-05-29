"""add_deleted_by_to_user

Revision ID: a2a59fbe5a70
Revises: 866b9dc21c90
Create Date: 2026-05-28 13:23:37.416073

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a2a59fbe5a70'
down_revision: Union[str, Sequence[str], None] = '866b9dc21c90'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.execute("""
        ALTER TABLE public."user"
        ADD COLUMN deleted_by VARCHAR(20) DEFAULT NULL
    """)

def downgrade() -> None:
    """Downgrade schema."""

    op.execute("""
        ALTER TABLE public."user"
        DROP COLUMN deleted_by
    """)
