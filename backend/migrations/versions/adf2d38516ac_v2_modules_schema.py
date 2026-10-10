"""v2_modules_schema

Revision ID: adf2d38516ac
Revises: 51b1e8b864ff
Create Date: 2026-10-10 17:46:57.177229

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'adf2d38516ac'
down_revision: Union[str, Sequence[str], None] = '51b1e8b864ff'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema for Version 2 modules."""
    json_type = sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), 'postgresql')

    # 1. Financial Models Table
    op.create_table(
        'financial_models',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False, server_default='Base Financial Plan'),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('currency', sa.String(length=10), nullable=False, server_default='USD'),
        sa.Column('forecast_months', sa.Integer(), nullable=False, server_default='12'),
        sa.Column('assumptions_json', json_type, nullable=False),
        sa.Column('projections_json', json_type, nullable=False),
        sa.Column('scenarios_json', json_type, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id', 'version', name='uq_project_financial_version')
    )
    op.create_index(op.f('ix_financial_models_project_id'), 'financial_models', ['project_id'], unique=False)
    op.create_index(op.f('ix_financial_models_user_id'), 'financial_models', ['user_id'], unique=False)

    # 2. Roadmap Tasks Table
    op.create_table(
        'roadmap_tasks',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('task_key', sa.String(length=50), nullable=False),
        sa.Column('milestone', sa.String(length=50), nullable=False),
        sa.Column('stage', sa.String(length=100), nullable=False, server_default='Research & Validation'),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('priority', sa.String(length=20), nullable=False, server_default='medium'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='not_started'),
        sa.Column('estimated_effort_days', sa.Float(), nullable=False, server_default='2.0'),
        sa.Column('start_day', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('duration_days', sa.Integer(), nullable=False, server_default='7'),
        sa.Column('dependencies_json', json_type, nullable=False),
        sa.Column('deliverable', sa.Text(), nullable=True),
        sa.Column('success_criteria', sa.Text(), nullable=True),
        sa.Column('related_risk', sa.Text(), nullable=True),
        sa.Column('kpi', sa.String(length=150), nullable=True),
        sa.Column('order_index', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_roadmap_tasks_project_id'), 'roadmap_tasks', ['project_id'], unique=False)
    op.create_index(op.f('ix_roadmap_tasks_user_id'), 'roadmap_tasks', ['user_id'], unique=False)
    op.create_index(op.f('ix_roadmap_tasks_task_key'), 'roadmap_tasks', ['task_key'], unique=False)

    # 3. Copilot Revisions Table
    op.create_table(
        'copilot_revisions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('target_module', sa.String(length=50), nullable=False),
        sa.Column('target_section', sa.String(length=100), nullable=False),
        sa.Column('action_type', sa.String(length=30), nullable=False, server_default='propose_edit'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('user_query', sa.Text(), nullable=False),
        sa.Column('proposal_content', json_type, nullable=False),
        sa.Column('previous_content', json_type, nullable=True),
        sa.Column('reasoning', sa.Text(), nullable=True),
        sa.Column('model', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_copilot_revisions_project_id'), 'copilot_revisions', ['project_id'], unique=False)
    op.create_index(op.f('ix_copilot_revisions_user_id'), 'copilot_revisions', ['user_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_copilot_revisions_user_id'), table_name='copilot_revisions')
    op.drop_index(op.f('ix_copilot_revisions_project_id'), table_name='copilot_revisions')
    op.drop_table('copilot_revisions')

    op.drop_index(op.f('ix_roadmap_tasks_task_key'), table_name='roadmap_tasks')
    op.drop_index(op.f('ix_roadmap_tasks_user_id'), table_name='roadmap_tasks')
    op.drop_index(op.f('ix_roadmap_tasks_project_id'), table_name='roadmap_tasks')
    op.drop_table('roadmap_tasks')

    op.drop_index(op.f('ix_financial_models_user_id'), table_name='financial_models')
    op.drop_index(op.f('ix_financial_models_project_id'), table_name='financial_models')
    op.drop_table('financial_models')
