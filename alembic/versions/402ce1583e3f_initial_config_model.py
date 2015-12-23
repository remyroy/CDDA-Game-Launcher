"""Initial config model

Revision ID: 402ce1583e3f
Revises: 
Create Date: 2015-12-23 15:05:36.841153

"""

# revision identifiers, used by Alembic.
revision = '402ce1583e3f'
down_revision = None
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('config_value',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(32), nullable=False, index=True),
        sa.Column('value', sa.Text(), nullable=False),
    )

    op.create_table('game_version',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('sha256', sa.String(64), nullable=False, index=True),
        sa.Column('version', sa.String(32), nullable=False),
    )


def downgrade():
    op.drop('game_version')
    op.drop('config_value')
