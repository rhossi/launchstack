"""add namespace to stacks

Revision ID: 002_add_namespace_to_stacks
Revises: 001_initial
Create Date: 2024-01-16 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002_add_namespace_to_stacks'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add namespace column (nullable initially for existing rows)
    op.add_column('stacks', sa.Column('namespace', sa.String(255), nullable=True))
    
    # Backfill namespace for existing stacks: f"stack-{id}"
    op.execute("""
        UPDATE stacks 
        SET namespace = 'stack-' || id::text
    """)
    
    # Make namespace NOT NULL and unique after backfill
    op.alter_column('stacks', 'namespace', nullable=False)
    op.create_index('idx_stacks_namespace', 'stacks', ['namespace'], unique=True)


def downgrade() -> None:
    op.drop_index('idx_stacks_namespace', table_name='stacks')
    op.drop_column('stacks', 'namespace')

