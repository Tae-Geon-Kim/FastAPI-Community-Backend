"""create_audit_logs_table

Revision ID: 8e281cde89a2
Revises: fcaa8c1883c3
Create Date: 2026-05-20 09:32:45.621126

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '8e281cde89a2'
down_revision: Union[str, Sequence[str], None] = 'fcaa8c1883c3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.execute("""
        CREATE TABLE IF NOT EXISTS public.audit_logs (
            id BIGSERIAL PRIMARY KEY,
            actor_user_index BIGINT,
            actor_user_id VARCHAR(100),
            action VARCHAR(100) NOT NULL,
            target_type VARCHAR(100) NOT NULL,
            target_index BIGINT NOT NULL,
            detail jsonb,
            reg_date TIMESTAMPTZ DEFAULT NOW()
        );
    """)

    op.create_index('idx_audit_actor', 'audit_logs', ['actor_user_index'])
    op.create_index('idx_audit_target', 'audit_logs', ['target_type', 'target_index'])
    op.create_index('idx_audit_reg_date', 'audit_logs', ['reg_date'])


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index('idx_audit_actor', table_name = 'audit_logs')
    op.drop_index('idx_audit_target', table_name = 'audit_logs')
    op.drop_index('idx_audit_reg_date', table_name = 'audit_logs')

    op.execute('DROP TABLE IF EXISTS public.audit_logs CASCADE;')