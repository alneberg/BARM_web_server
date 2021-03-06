"""empty message

Revision ID: 15045c53040
Revises: 80bab4f8ff
Create Date: 2016-01-07 10:21:05.812275

"""

# revision identifiers, used by Alembic.
revision = '15045c53040'
down_revision = '80bab4f8ff'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('annotation',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('annotation_type', sa.String(), nullable=True),
    sa.Column('type_identifier', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('annotation_type', 'type_identifier', name='annotation_unique')
    )
    op.create_table('annotation_source',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('dbname', sa.String(), nullable=True),
    sa.Column('dbversion', sa.String(), nullable=True),
    sa.Column('algorithm', sa.String(), nullable=True),
    sa.Column('algorithm_parameters', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('reference_assembly',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('cog',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('category', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['id'], ['annotation.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('ecnumber',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('first_digit', sa.Integer(), nullable=True),
    sa.Column('second_digit', sa.Integer(), nullable=True),
    sa.Column('third_digit', sa.Integer(), nullable=True),
    sa.Column('fourth_digit', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['id'], ['annotation.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ecnumber_first_digit'), 'ecnumber', ['first_digit'], unique=False)
    op.create_index(op.f('ix_ecnumber_fourth_digit'), 'ecnumber', ['fourth_digit'], unique=False)
    op.create_index(op.f('ix_ecnumber_second_digit'), 'ecnumber', ['second_digit'], unique=False)
    op.create_index(op.f('ix_ecnumber_third_digit'), 'ecnumber', ['third_digit'], unique=False)
    op.create_table('gene',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('reference_assemlby_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['reference_assemlby_id'], ['reference_assembly.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('pfam',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['id'], ['annotation.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('tigrfam',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['id'], ['annotation.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('gene_annotation',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('annotation_id', sa.Integer(), nullable=True),
    sa.Column('gene_id', sa.Integer(), nullable=True),
    sa.Column('e_value', sa.Float(), nullable=True),
    sa.Column('annotation_source_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['annotation_id'], ['annotation.id'], ),
    sa.ForeignKeyConstraint(['annotation_source_id'], ['annotation_source.id'], ),
    sa.ForeignKeyConstraint(['gene_id'], ['gene.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('gene_id', 'annotation_id', 'annotation_source_id', name='gene_annotation_unique')
    )
    op.create_table('gene_count',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('sample_id', sa.Integer(), nullable=False),
    sa.Column('gene_id', sa.Integer(), nullable=False),
    sa.Column('rpkm', sa.Float(), nullable=True),
    sa.ForeignKeyConstraint(['gene_id'], ['gene.id'], ),
    sa.ForeignKeyConstraint(['sample_id'], ['sample.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('sample_id', 'gene_id', name='genecount_unique')
    )
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('gene_count')
    op.drop_table('gene_annotation')
    op.drop_table('tigrfam')
    op.drop_table('pfam')
    op.drop_table('gene')
    op.drop_index(op.f('ix_ecnumber_third_digit'), table_name='ecnumber')
    op.drop_index(op.f('ix_ecnumber_second_digit'), table_name='ecnumber')
    op.drop_index(op.f('ix_ecnumber_fourth_digit'), table_name='ecnumber')
    op.drop_index(op.f('ix_ecnumber_first_digit'), table_name='ecnumber')
    op.drop_table('ecnumber')
    op.drop_table('cog')
    op.drop_table('reference_assembly')
    op.drop_table('annotation_source')
    op.drop_table('annotation')
    ### end Alembic commands ###
