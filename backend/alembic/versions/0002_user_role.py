"""add users.role, stored by value

Revision ID: 0002_user_role
Revises: 0001_baseline
Create Date: 2026-10-25 15:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0002_user_role'
down_revision: Union[str, Sequence[str], None] = '0001_baseline'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # The server default fills existing rows, so the column can be NOT NULL at once.
    op.add_column(
        'users',
        sa.Column('role', sa.String(length=20), server_default='default', nullable=False),
    )
    op.create_check_constraint(
        'user_role', 'users', "role IN ('admin', 'moderator', 'default')"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('user_role', 'users', type_='check')
    op.drop_column('users', 'role')
