"""security_hardening
Revision ID: c7b2a1d4e8f3
Revises: adf2d38516ac
Create Date: 2026-10-12 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'c7b2a1d4e8f3'
down_revision: Union[str, Sequence[str], None] = 'adf2d38516ac'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create tables for session revocation and distributed rate limiting."""
    # 1. Revoked Sessions Table
    op.create_table(
        'revoked_sessions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('session_id', sa.String(length=64), nullable=True),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('revoked_before', sa.DateTime(timezone=True), nullable=True),
        sa.Column('exempt_session_id', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_revoked_sessions_session_id'), 'revoked_sessions', ['session_id'], unique=False)
    op.create_index(op.f('ix_revoked_sessions_user_id'), 'revoked_sessions', ['user_id'], unique=False)
    op.create_index(op.f('ix_revoked_sessions_expires_at'), 'revoked_sessions', ['expires_at'], unique=False)

    # 2. Rate Limit Entries Table
    op.create_table(
        'rate_limit_entries',
        sa.Column('key', sa.String(length=255), nullable=False),
        sa.Column('attempts', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('window_start', sa.Float(), nullable=False),
        sa.Column('expires_at', sa.Float(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('key'),
    )
    op.create_index(op.f('ix_rate_limit_entries_expires_at'), 'rate_limit_entries', ['expires_at'], unique=False)


def downgrade() -> None:
    """Drop tables for session revocation and distributed rate limiting."""
    op.drop_index(op.f('ix_rate_limit_entries_expires_at'), table_name='rate_limit_entries')
    op.drop_table('rate_limit_entries')

    op.drop_index(op.f('ix_revoked_sessions_expires_at'), table_name='revoked_sessions')
    op.drop_index(op.f('ix_revoked_sessions_user_id'), table_name='revoked_sessions')
    op.drop_index(op.f('ix_revoked_sessions_session_id'), table_name='revoked_sessions')
    op.drop_table('revoked_sessions')
