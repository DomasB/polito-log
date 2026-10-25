"""hash magic link tokens

Revision ID: 0006_magic_link_token_hash
Revises: 0005_token_version
Create Date: 2026-10-25 14:58:14.495667

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0006_magic_link_token_hash'
down_revision: Union[str, Sequence[str], None] = '0005_token_version'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Hash the existing tokens in place, so links already emailed keep working.
    # sha256() is built into PostgreSQL 11+.
    op.drop_index('ix_magic_links_token', table_name='magic_links')
    op.alter_column('magic_links', 'token', new_column_name='token_hash')
    op.execute("UPDATE magic_links SET token_hash = encode(sha256(convert_to(token_hash, 'UTF8')), 'hex')")
    op.alter_column(
        'magic_links', 'token_hash',
        type_=sa.String(length=64), existing_type=sa.String(length=255), existing_nullable=False,
    )
    op.create_index(op.f('ix_magic_links_token_hash'), 'magic_links', ['token_hash'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    # Plaintext tokens cannot be recovered: outstanding links stop working.
    op.drop_index(op.f('ix_magic_links_token_hash'), table_name='magic_links')
    op.execute("UPDATE magic_links SET is_used = true")
    op.alter_column(
        'magic_links', 'token_hash', new_column_name='token',
        type_=sa.String(length=255), existing_type=sa.String(length=64), existing_nullable=False,
    )
    op.create_index('ix_magic_links_token', 'magic_links', ['token'], unique=True)
