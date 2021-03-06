"""empty message

Revision ID: 871ea0f5e7b4
Revises: 
Create Date: 2019-09-25 14:36:07.493032

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '871ea0f5e7b4'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('country',
    sa.Column('id', sa.String(length=10), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('service',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('description', sa.String(length=255), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('email', sa.String(length=120), nullable=False),
    sa.Column('company', sa.String(length=120), nullable=False),
    sa.Column('tel', sa.String(length=120), nullable=False),
    sa.Column('address1', sa.String(length=255), nullable=True),
    sa.Column('address2', sa.String(length=255), nullable=True),
    sa.Column('city', sa.String(length=50), nullable=True),
    sa.Column('state', sa.String(length=50), nullable=True),
    sa.Column('zip', sa.String(length=50), nullable=True),
    sa.Column('country', sa.String(length=50), nullable=True),
    sa.Column('password', sa.String(length=60), nullable=False),
    sa.Column('verified', sa.Boolean(), nullable=True),
    sa.Column('role', sa.Integer(), nullable=False),
    sa.Column('date_registered', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email'),
    sa.UniqueConstraint('name')
    )
    op.create_table('admin_item',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('item_type', sa.Boolean(), nullable=True),
    sa.Column('matched_item', sa.Integer(), nullable=False),
    sa.Column('service_id', sa.Integer(), nullable=False),
    sa.Column('function', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['service_id'], ['service.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('client_item',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('item_type', sa.Boolean(), nullable=True),
    sa.Column('matched_item', sa.Integer(), nullable=False),
    sa.Column('service_id', sa.Integer(), nullable=False),
    sa.Column('function', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['service_id'], ['service.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('user_service',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('service_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('project_name', sa.String(length=100), nullable=False),
    sa.ForeignKeyConstraint(['service_id'], ['service.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('a_item',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('item_type', sa.Boolean(), nullable=True),
    sa.Column('form_text', sa.String(length=255), nullable=True),
    sa.Column('user_service_id', sa.Integer(), nullable=False),
    sa.Column('function', sa.Integer(), nullable=False),
    sa.Column('filename', sa.String(length=255), nullable=True),
    sa.Column('date', sa.Date(), nullable=True),
    sa.Column('checked', sa.Boolean(), nullable=True),
    sa.Column('updated', sa.DateTime(), nullable=True),
    sa.Column('finished', sa.Boolean(), nullable=True),
    sa.Column('finished_time', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_service_id'], ['user_service.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('c_item',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('item_type', sa.Boolean(), nullable=True),
    sa.Column('form_text', sa.String(length=255), nullable=True),
    sa.Column('user_service_id', sa.Integer(), nullable=False),
    sa.Column('function', sa.Integer(), nullable=False),
    sa.Column('filename', sa.String(length=255), nullable=True),
    sa.Column('date', sa.Date(), nullable=True),
    sa.Column('checked', sa.Boolean(), nullable=True),
    sa.Column('updated', sa.DateTime(), nullable=True),
    sa.Column('finished', sa.Boolean(), nullable=True),
    sa.Column('finished_time', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_service_id'], ['user_service.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('c_item')
    op.drop_table('a_item')
    op.drop_table('user_service')
    op.drop_table('client_item')
    op.drop_table('admin_item')
    op.drop_table('user')
    op.drop_table('service')
    op.drop_table('country')
    # ### end Alembic commands ###
