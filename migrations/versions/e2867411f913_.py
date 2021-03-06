"""empty message

Revision ID: e2867411f913
Revises: dca22f874919
Create Date: 2018-04-11 10:30:26.799729

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e2867411f913'
down_revision = 'dca22f874919'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('social_o_auth', sa.Column('source', sa.String(), nullable=True))
    op.add_column('user', sa.Column('avatar_URL', sa.String(), nullable=True))
    op.drop_column('user', 'avatar')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('avatar', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.drop_column('user', 'avatar_URL')
    op.drop_column('social_o_auth', 'source')
    # ### end Alembic commands ###
