"""add_user_status_boards_category

Revision ID: 8d22fa7ebe60
Revises: abc6689d37a8
Create Date: 2026-05-12 10:32:29.374914

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8d22fa7ebe60'
down_revision: Union[str, Sequence[str], None] = 'abc6689d37a8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    
    op.add_column(
        "user",
        sa.Column("status", sa.String(), nullable = False, server_default = "ACTIVE")
    )

    op.add_column(
        "boards",
        sa.Column("category", sa.String(), nullable = False, server_default = "GENERAL")
    )


def downgrade() -> None:
    """Downgrade schema."""
    
    op.drop_column("boards", "category")

    op.drop_column("user", "status")