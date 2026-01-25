"""Add is_base_type to ProjectType

Revision ID: 5c2052a7c3c4
Revises: 0d227417b23b
Create Date: 2026-01-24 11:39:59.818447

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5c2052a7c3c4'
down_revision = '0d227417b23b'
branch_labels = None
depends_on = None


def upgrade():
    # Add is_base_type column with default False
    op.add_column(
        'marketplace_project_type',
        sa.Column('is_base_type', sa.Boolean(), nullable=False, server_default='0')
    )

    # Set einzelkunde as the base type
    op.execute(
        "UPDATE marketplace_project_type SET is_base_type = 1 WHERE code = 'einzelkunde'"
    )


def downgrade():
    op.drop_column('marketplace_project_type', 'is_base_type')
