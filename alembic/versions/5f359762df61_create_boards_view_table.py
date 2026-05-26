"""create_boards_view_table

Revision ID: 5f359762df61
Revises: 8e281cde89a2
Create Date: 2026-05-21 14:47:31.095407

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5f359762df61'
down_revision: Union[str, Sequence[str], None] = '8e281cde89a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    
    op.execute("""
        CREATE TABLE IF NOT EXISTS public.boards_view(
            view_id BIGSERIAL PRIMARY KEY,
            board_index BIGINT NOT NULL,
            user_index BIGINT NULL,
            anonymous_id UUID NULL,
            viewed_at TIMESTAMPTZ DEFAULT NOW(),

            CONSTRAINT fk_board
                FOREIGN KEY (board_index)
                REFERENCES boards(index)
                ON DELETE CASCADE,
            
            CONSTRAINT fk_user
                FOREIGN KEY (user_index)
                REFERENCES "user"(index)
                ON DELETE SET NULL
        );
    """)

    op.create_index('idx_user_view', 'boards_view', ['board_index', 'user_index'])
    op.create_index('idx_anonymous_view', 'boards_view', ['board_index', 'anonymous_id'])
    op.create_index('idx_viewed_at', 'boards_view', ['viewed_at'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_user_view', table_name = 'boards_view')
    op.drop_index('idx_anonymous_view', table_name = 'boards_view')
    op.drop_index('idx_viewed_at', table_name = 'boards_view')
    
    op.execute('DROP TABLE IF EXISTS public.boards_view CASCADE;')
