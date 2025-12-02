"""add graph_id to agents

Revision ID: 005_add_graph_id_to_agents
Revises: 004_add_status_to_stacks
Create Date: 2025-01-27 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '005_add_graph_id_to_agents'
down_revision: Union[str, None] = '004_add_status_to_stacks'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add graph_id column (nullable initially, can be made non-nullable later)
    op.add_column('agents', sa.Column('graph_id', sa.String(255), nullable=True))
    
    # Create index on graph_id for lookups
    op.create_index('idx_agents_graph_id', 'agents', ['graph_id'])


def downgrade() -> None:
    op.drop_index('idx_agents_graph_id', table_name='agents')
    op.drop_column('agents', 'graph_id')

