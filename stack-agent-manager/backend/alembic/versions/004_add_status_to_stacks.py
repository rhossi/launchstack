"""add status to stacks

Revision ID: 004_add_status_to_stacks
Revises: 003_add_agent_deployment_fields
Create Date: 2025-11-25 18:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '004_add_status_to_stacks'
down_revision: Union[str, None] = '003_add_agent_deployment_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add status column with default
    op.add_column('stacks', sa.Column('status', sa.String(50), nullable=False, server_default='ready'))
    
    # Create index on status for filtering
    op.create_index('idx_stacks_status', 'stacks', ['status'])


def downgrade() -> None:
    op.drop_index('idx_stacks_status', table_name='stacks')
    op.drop_column('stacks', 'status')

