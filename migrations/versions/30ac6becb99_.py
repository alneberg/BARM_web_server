"""empty message

Revision ID: 30ac6becb99
Revises: None
Create Date: 2015-11-11 18:06:52.911161

"""

# revision identifiers, used by Alembic.
revision = '30ac6becb99'
down_revision = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('sample_set',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('time_place',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('time', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('sample',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('scilifelab_code', sa.String(length=11), nullable=True),
    sa.Column('sample_set_id', sa.Integer(), nullable=True),
    sa.Column('timeplace_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['sample_set_id'], ['sample_set.id'], ),
    sa.ForeignKeyConstraint(['timeplace_id'], ['time_place.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('sample_property',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('value', sa.String(), nullable=True),
    sa.Column('datatype', sa.String(), nullable=True),
    sa.Column('sample_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['sample_id'], ['sample.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sample_property_name'), 'sample_property', ['name'], unique=False)
    op.create_index(op.f('ix_sample_property_value'), 'sample_property', ['value'], unique=False)
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_sample_property_value'), table_name='sample_property')
    op.drop_index(op.f('ix_sample_property_name'), table_name='sample_property')
    op.drop_table('sample_property')
    op.drop_table('sample')
    op.drop_table('time_place')
    op.drop_table('sample_set')
    ### end Alembic commands ###
