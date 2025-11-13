"""add_user_roles

Revision ID: dead8375eec4
Revises: 
Create Date: 2025-11-13 07:44:56.330387

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dead8375eec4'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add role column as nullable first
    op.add_column('users', sa.Column('role', sa.String(length=20), nullable=True))

    # Set default value for existing users
    op.execute("UPDATE users SET role = 'default' WHERE role IS NULL")

    # Make the column non-nullable
    op.alter_column('users', 'role', nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Remove role column
    op.drop_column('users', 'role')
