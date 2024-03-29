"""empty message

Revision ID: c7a1db56f747
Revises: 45650a5987ea
Create Date: 2023-06-14 15:21:23.803743

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'c7a1db56f747'
down_revision = '45650a5987ea'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    money_mode_enum = postgresql.ENUM('REAL', 'PAPER', 'NOT_CONFIGURED', name='botmoneymode', create_type=False)
    money_mode_enum.create(op.get_bind(), checkfirst=True)

    return_type_enum = postgresql.ENUM('LOG_RETURN', 'RETURN', name='returntype', create_type=False)
    return_type_enum.create(op.get_bind(), checkfirst=True)

    op.add_column('Bots', sa.Column('money_mode', money_mode_enum, nullable=True))
    op.add_column('Bots', sa.Column('return_type', return_type_enum, nullable=True))
    op.create_unique_constraint(None, 'Stocks', ['name'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'Stocks', type_='unique')
    op.drop_column('Bots', 'return_type')
    op.drop_column('Bots', 'money_mode')
    # ### end Alembic commands ###
