# SPDX-FileCopyrightText: 2015-2021 Rémy Roy
#
# SPDX-License-Identifier: MIT

"""stable versions

Revision ID: 0e35fff276f3
Revises: 402ce1583e3f
Create Date: 2019-08-26 10:55:16.968432

"""

# revision identifiers, used by Alembic.
revision = '0e35fff276f3'
down_revision = '402ce1583e3f'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa

def upgrade():
    with op.batch_alter_table("game_version") as batch_op:
        batch_op.add_column(sa.Column('stable', sa.Boolean, nullable=True))

    op.execute('UPDATE game_version SET stable = 0')

    with op.batch_alter_table("game_version") as batch_op:
        batch_op.alter_column('stable', nullable=False)

    op.execute("UPDATE game_version SET stable = 1 WHERE sha256 in ("
        "'2d7bbf426572e2b21aede324c8d89c9ad84529a05a4ac99a914f22b2b1e1405e',"
        "'0454ed2bbc4a6c1c8cca5c360533513eb2a1d975816816d7c13ff60e276d431b',"
        "'7f914145248cebfd4d1a6d4b1ff932a478504b1e7e4c689aab97b8700e079f61')")

def downgrade():
    with op.batch_alter_table("game_version") as batch_op:
        batch_op.drop_column('stable')
