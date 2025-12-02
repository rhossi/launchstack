"""add agent deployment fields

Revision ID: 003_add_agent_deployment_fields
Revises: 002_add_namespace_to_stacks
Create Date: 2024-01-16 10:01:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '003_add_agent_deployment_fields'
down_revision: Union[str, None] = '002_add_namespace_to_stacks'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add status column with default
    op.add_column('agents', sa.Column('status', sa.String(50), nullable=False, server_default='pending'))
    
    # Add URL columns (nullable)
    op.add_column('agents', sa.Column('api_url', sa.String(500), nullable=True))
    op.add_column('agents', sa.Column('ui_url', sa.String(500), nullable=True))
    
    # Add disk_path column (nullable)
    op.add_column('agents', sa.Column('disk_path', sa.String(1000), nullable=True))
    
    # Create index on status for filtering
    op.create_index('idx_agents_status', 'agents', ['status'])


def downgrade() -> None:
    op.drop_index('idx_agents_status', table_name='agents')
    op.drop_column('agents', 'disk_path')
    op.drop_column('agents', 'ui_url')
    op.drop_column('agents', 'api_url')
    op.drop_column('agents', 'status')

