"""empty message

Revision ID: c201e0cbbd47
Revises: 59eef35f1505
Create Date: 2023-06-23 03:41:23.459447

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'c201e0cbbd47'
down_revision = '59eef35f1505'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('Bots', 'running_mode')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Bots', sa.Column('running_mode', postgresql.ENUM('MINUTE', 'HOUR', 'DAY', name='investmentintervalscale'), autoincrement=False, nullable=True))
    # ### end Alembic commands ###
