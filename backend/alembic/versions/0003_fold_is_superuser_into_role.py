"""fold users.is_superuser into users.role

Revision ID: 0003_fold_is_superuser
Revises: 0002_user_role
Create Date: 2026-10-25 15:30:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0003_fold_is_superuser'
down_revision: Union[str, Sequence[str], None] = '0002_user_role'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("UPDATE users SET role = 'admin' WHERE is_superuser")
    op.drop_column('users', 'is_superuser')


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column(
        'users',
        sa.Column('is_superuser', sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.execute("UPDATE users SET is_superuser = true WHERE role = 'admin'")
    op.alter_column('users', 'is_superuser', server_default=None)
