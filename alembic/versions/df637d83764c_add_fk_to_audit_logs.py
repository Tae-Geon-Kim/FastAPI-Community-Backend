"""add_fk_to_audit_logs

Revision ID: df637d83764c
Revises: 5f359762df61
Create Date: 2026-05-21 15:55:26.673240

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'df637d83764c'
down_revision: Union[str, Sequence[str], None] = '5f359762df61'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    
    op.create_foreign_key(
        'fk_audit_user',         
        source_table = 'audit_logs',
        referent_table = 'user',
        local_cols = ['actor_user_index'], 
        remote_cols = ['index'],
        ondelete = 'SET NULL'
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_constraint('fk_audit_user', table_name='audit_logs', type_='foreignkey')