"""add_deleted_by_to_files

Revision ID: 866b9dc21c90
Revises: 742bceab28da
Create Date: 2026-05-27 13:24:35.031527

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '866b9dc21c90'
down_revision: Union[str, Sequence[str], None] = '742bceab28da'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.execute("""
        ALTER TABLE public.files
        ADD COLUMN deleted_by VARCHAR(20) DEFAULT NULL
    """)


def downgrade() -> None:
    """Downgrade schema."""

    op.execute("""
        ALTER TABLE public.files
        DROP COLUMN deleted_by
    """)

