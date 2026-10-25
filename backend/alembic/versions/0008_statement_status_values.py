"""store statements.status by value, add 'rejected'

The column was a native Postgres enum (statementstatus) holding member names
('PENDING'). It becomes VARCHAR(20) holding values ('pending'), guarded by a
CHECK constraint, the same way users.role is stored (0002_user_role).

Downgrade restores the native enum. It has no 'rejected' label, so rejected
statements become pending on downgrade: that mapping is lossy.

Revision ID: 0008_statement_status_values
Revises: 0007_magic_link_request_ip
Create Date: 2026-10-25 18:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '0008_statement_status_values'
down_revision: Union[str, Sequence[str], None] = '0007_magic_link_request_ip'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

OLD_ENUM = postgresql.ENUM(
    'PENDING', 'VERIFIED', 'DISPUTED', 'RETRACTED', name='statementstatus'
)


def upgrade() -> None:
    """Upgrade schema."""
    # Converts every row: 'PENDING' -> 'pending'. ix_statements_status is rebuilt.
    op.alter_column(
        'statements',
        'status',
        type_=sa.String(length=20),
        existing_nullable=False,
        postgresql_using='lower(status::text)',
    )
    OLD_ENUM.drop(op.get_bind(), checkfirst=True)
    op.create_check_constraint(
        'statement_status',
        'statements',
        "status IN ('pending', 'verified', 'disputed', 'retracted', 'rejected')",
    )


def downgrade() -> None:
    """Downgrade schema. Rejected statements become pending (lossy)."""
    op.drop_constraint('statement_status', 'statements', type_='check')
    op.execute("UPDATE statements SET status = 'pending' WHERE status = 'rejected'")
    OLD_ENUM.create(op.get_bind(), checkfirst=True)
    op.alter_column(
        'statements',
        'status',
        type_=OLD_ENUM,
        existing_nullable=False,
        postgresql_using='upper(status)::statementstatus',
    )
