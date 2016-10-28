"""empty message

Revision ID: cfa84823246a
Revises: 7ce3ce94c8ea
Create Date: 2016-07-19 17:46:11.968614

"""

# revision identifiers, used by Alembic.
revision = 'cfa84823246a'
down_revision = '7ce3ce94c8ea'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_index(op.f('ix_gene_taxon_id'), 'gene', ['taxon_id'], unique=False)
    op.create_index(op.f('ix_taxon_full_taxonomy'), 'taxon', ['full_taxonomy'], unique=False)
    op.create_index(op.f('ix_taxon_id'), 'taxon', ['id'], unique=False)
    op.create_index(op.f('ix_taxon_up_to_family'), 'taxon', ['up_to_family'], unique=False)
    op.create_index(op.f('ix_taxon_up_to_genus'), 'taxon', ['up_to_genus'], unique=False)
    op.create_index(op.f('ix_taxon_up_to_order'), 'taxon', ['up_to_order'], unique=False)
    op.create_index(op.f('ix_taxon_up_to_phylum'), 'taxon', ['up_to_phylum'], unique=False)
    op.create_index(op.f('ix_taxon_up_to_species'), 'taxon', ['up_to_species'], unique=False)
    op.create_index(op.f('ix_taxon_up_to_superkingdom'), 'taxon', ['up_to_superkingdom'], unique=False)
    op.create_index(op.f('ix_taxon_up_to_taxclass'), 'taxon', ['up_to_taxclass'], unique=False)
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_taxon_up_to_taxclass'), table_name='taxon')
    op.drop_index(op.f('ix_taxon_up_to_superkingdom'), table_name='taxon')
    op.drop_index(op.f('ix_taxon_up_to_species'), table_name='taxon')
    op.drop_index(op.f('ix_taxon_up_to_phylum'), table_name='taxon')
    op.drop_index(op.f('ix_taxon_up_to_order'), table_name='taxon')
    op.drop_index(op.f('ix_taxon_up_to_genus'), table_name='taxon')
    op.drop_index(op.f('ix_taxon_up_to_family'), table_name='taxon')
    op.drop_index(op.f('ix_taxon_id'), table_name='taxon')
    op.drop_index(op.f('ix_taxon_full_taxonomy'), table_name='taxon')
    op.drop_index(op.f('ix_gene_taxon_id'), table_name='gene')
    ### end Alembic commands ###