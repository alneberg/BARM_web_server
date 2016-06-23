import app
from models import *
import pandas as pd
import argparse
import os
import sys
import logging
import datetime
import numpy as np

from materialized_view_factory import refresh_all_mat_views

logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)

def main(args):
    # Create materialized view that is not created by manage.py
    app.db.create_all()

    # connect to database
    session = app.db.session()

    logging.info("Reading sample information")
    # Add all samples from the sample info file
    sample_info = pd.read_table(args.sample_info, sep=',', index_col=0)

    logging.info("Creating sample sets")
    # sample_set
    sample_sets = {}
    for sample_set_name, sample_set_df in sample_info.groupby('sample_set'):
        if len(SampleSet.query.filter_by(name=sample_set_name).all()) == 0:
            sample_set = SampleSet(sample_set_name)
        for sample_id, row in sample_set_df.iterrows():
            sample_sets[sample_id] = sample_set

    logging.info("Creating individual samples")
    sample_properties = []
    all_samples = {}
    time_places = []
    metadata_reference = pd.read_table(args.metadata_reference, index_col=0)
    meta_categories = list(metadata_reference.index)
    default_units = metadata_reference['Unit'].to_dict()
    default_units['filter_lower'] = 'µm'
    default_units['filter_upper'] = 'µm'
    for sample_id, row in sample_info.iterrows():
        samples_with_code = Sample.query.filter_by(scilifelab_code=sample_id).all()
        assert len(samples_with_code) == 0

        meta_data = {}

        for meta_category in meta_categories:
            if meta_category == 'Collection date':
                date = datetime.datetime.strptime(row[meta_category], '%y/%m/%d')
            if meta_category == 'Collection time':
                time = datetime.datetime.strptime(str(row[meta_category]), '%H:%M').time()
            else:
                meta_data[meta_category] = row[meta_category]

        extra_categories = ['filter_lower', 'filter_upper']
        for meta_category in extra_categories:
            meta_data[meta_category] = row[meta_category]

        time_place = TimePlace(datetime.datetime.combine(date, time), meta_data['Latitude'], meta_data['Longitude'])
        time_places.append(time_place)

        all_samples[sample_id] = Sample(sample_id, sample_sets[sample_id], time_place)

        for meta_category in meta_categories:
            if meta_category in ['Latitude', 'Longitude', 'Collection date', 'Collection time']:
                continue
            if meta_data[meta_category] is not None:
                sample_properties.append(SampleProperty(meta_category, meta_data[meta_category], default_units[meta_category], all_samples[sample_id]))

    session.add_all(list(sample_sets.values()) + list(all_samples.values()) + time_places + sample_properties)

    logging.info("Creating the reference assembly")
    # create the reference assembly
    ref_assemblies = ReferenceAssembly.query.filter_by(name=args.reference_assembly).all()
    if len(ref_assemblies) == 0:
        ref_assembly = ReferenceAssembly(args.reference_assembly)
    else:
        assert len(ref_assemblies) == 1
        ref_assembly = ref_assemlbies[0]

    session.add(ref_assembly)

    logging.info("Adding annotation information")
    # Make sure annotations are present
    annotation_info = pd.read_table(args.all_annotations, header=None, names=["type_identifier", "gene_name", "description"])
    annotation_models = {'COG': Cog, 'TIG': TigrFam, 'pfa': Pfam, 'PFA': Pfam}
    annotation_polymorphic_id = {'COG': 'cog', 'TIG': 'tigrfam', 'pfa': 'pfam', 'PFA': 'pfam'}

    all_annotations = {}
    annotation_info['annotation_type'] = annotation_info['type_identifier'].apply(lambda x: annotation_polymorphic_id[x[0:3]])
    annotation_info['type_grouping'] = annotation_info['type_identifier'].apply(lambda x: x[0:3])
    annotation_info['id'] = annotation_info.index
    annotation_info['category'] = None
    for type_grouping, annotation_info_subset in annotation_info.groupby('type_grouping'):
        if type_grouping == 'COG':
            logging.info("Commiting all COG annotation info")
            session.bulk_insert_mappings(Cog, annotation_info_subset[['id', 'type_identifier', 'annotation_type', 'category', 'description']].to_dict(orient='index').values())
        else:
            logging.info("Commiting all {} annotation info".format(type_grouping))
            session.bulk_insert_mappings(annotation_models[type_grouping], annotation_info_subset[['id', 'type_identifier', 'annotation_type', 'description']].to_dict(orient='index').values())
    all_annotations = dict( (annotation.type_identifier, annotation) for annotation in session.query(Annotation).all() )

    logging.info("Adding annotation source")
    # Create annotation source
    annotation_source_info = pd.read_table(args.annotation_source_info, sep=',', header=None, names=["annotation_type", "db_version", "algorithm", "algorithm_parameters"], index_col = 0)
    all_annotation_sources = {}
    for annotation_type, row in annotation_source_info.iterrows():
        all_annotation_sources[annotation_type] = AnnotationSource(annotation_type, row.db_version, row.algorithm, row.algorithm_parameters)

    session.add_all(list(all_annotation_sources.values()))


    logging.info("Commiting everything except genes and gene counts")
    session.commit()

    commited_genes = {}
    def add_genes_with_annotation(annotation_type, gene_annotation_arg, commited_genes, all_annotations, annotation_source):
        logging.info("Adding genes with {} annotations".format(annotation_type))
        gene_annotations = pd.read_table(gene_annotation_arg, header=None, names=["name", "type_identifier", "e_value"])

        # Only add genes once
        new_genes = gene_annotations[ ~ gene_annotations['name'].isin(commited_genes.keys()) ]

        new_genes_uniq = pd.DataFrame([new_genes['name'].unique()])
        new_genes_uniq = new_genes_uniq.transpose()
        new_genes_uniq.columns = ['name']
        new_genes_uniq["reference_assembly_id"] = ref_assembly.id

        logging.info("Commiting all {} genes.".format(annotation_type))

        with open(args.tmp_file, 'w') as gene_file:
            new_genes_uniq[['name', 'reference_assembly_id']].to_csv(gene_file, index=False, header=False)
        session.execute("COPY gene (name, reference_assembly_id) FROM '{}' WITH CSV;".format(args.tmp_file))

        commited_genes.update(dict( session.query(Gene.name, Gene.id).all() ))
        logging.info("{} genes present in database".format(len(commited_genes.keys())))

        gene_annotations['gene_id'] = gene_annotations['name'].apply(lambda x: commited_genes[x])
        gene_annotations['annotation_id'] = gene_annotations['type_identifier'].apply(lambda x: all_annotations[x].id)

        annotation_source = all_annotation_sources[annotation_type]
        gene_annotations['annotation_source_id'] = annotation_source.id

        logging.info("Commiting all {} gene anntations".format(annotation_type))
        with open(args.tmp_file, 'w') as gene_file:
            gene_annotations[['gene_id', 'annotation_id', 'annotation_source_id', 'e_value']].to_csv(gene_file, index=False, header=False)
        session.execute("COPY gene_annotation (gene_id, annotation_id, annotation_source_id, e_value) FROM '{}' WITH CSV;".format(args.tmp_file))
        session.commit()
        return commited_genes

    commited_genes = add_genes_with_annotation("Cog", args.gene_annotations_cog, commited_genes, all_annotations, all_annotation_sources["Cog"])
    commited_genes = add_genes_with_annotation("Pfam", args.gene_annotations_pfam, commited_genes, all_annotations, all_annotation_sources["Pfam"])
    commited_genes = add_genes_with_annotation("TigrFam", args.gene_annotations_tigrfam, commited_genes, all_annotations, all_annotation_sources["TigrFam"])


    def add_genes_with_taxonomy(taxonomy_per_gene, commited_genes):
        gene_annotations = pd.read_table(taxonomy_per_gene, index_col=0)

        gene_annotations['taxclass'] = gene_annotations['class']

        # Only add genes with taxonomy given
        taxonomy_columns = ["superkingdom", "phylum", "taxclass", "order", "family", "genus", "species"]

        annotated_genes = gene_annotations[ ~ gene_annotations[taxonomy_columns].isnull().all(axis=1)]

        # Only add genes once
        new_genes = annotated_genes[ ~ annotated_genes.index.isin(commited_genes.keys()) ]

        new_genes_uniq = pd.DataFrame([list(new_genes.index)])
        new_genes_uniq = new_genes_uniq.transpose()
        new_genes_uniq.columns = ['name']
        new_genes_uniq["reference_assembly_id"] = ref_assembly.id

        logging.info("Commiting all {} genes.".format(annotation_type))

        with open(args.tmp_file, 'w') as gene_file:
            new_genes_uniq[['name', 'reference_assembly_id']].to_csv(gene_file, index=False, header=False)
        session.execute("COPY gene (name, reference_assembly_id) FROM '{}' WITH CSV;".format(args.tmp_file))

        commited_genes.update(dict( session.query(Gene.name, Gene.id).all() ))
        logging.info("{} genes present in database".format(len(commited_genes.keys())))

        def get_taxa_or_create(row, added_taxa, taxonomy_columns):
            t = tuple([ row[col] for col in taxonomy_columns])
            if t in added_taxa:
                return added_taxa[t], added_taxa
            first = True
            # We want to make a difference between unnamed phyla and unset phyla
            for column in reversed(taxonomy_columns):
                if row[column] is np.nan:
                    if first:
                        row[column] = None
                    else:
                        row[column] = "Unnamed"
                else:
                    first = False
            new_taxa = Taxon(**row[taxonomy_columns].to_dict())
            session.add(new_taxa)
            session.commit()
            added_taxa[t] = new_taxa
            return new_taxa, added_taxa

        added_taxa = {}
        gene_to_taxa = {}
        for gene_name, row in annotated_genes.iterrows():
            taxa, added_taxa = get_taxa_or_create(row, added_taxa, taxonomy_columns)
            gene_id = commited_genes[gene_name]
            gene_to_taxa[gene_id] = taxa

        logging.info("Updating genes with taxon information")
        genes_to_be_updated = []
        for gene_id, taxon in gene_to_taxa.items():
            gene = Gene.query.get(gene_id)
            gene.taxon = taxon
            genes_to_be_updated.append(gene)
        session.add_all(genes_to_be_updated)
        session.commit()

        return commited_genes

    logging.info("Processed {} genes for annotations, moving on to gene taxonomy".format(len(commited_genes.keys())))

    commited_genes = add_genes_with_taxonomy(args.taxonomy_per_gene, commited_genes)

    logging.info("Processed {} genes in total, moving on to gene counts".format(len(commited_genes.keys())))

    # Fetch each gene from the gene count file and create the corresponding gene count
    logging.info("Adding gene counts")
    gene_counts = pd.read_table(args.gene_counts, index_col=0)
    total_gene_count_len = len(gene_counts)
    val_cols = gene_counts.columns
    nr_columns = len(val_cols)

    filtered_gene_counts = gene_counts[ gene_counts.index.isin(commited_genes.keys()) ].copy()
    filtered_gene_counts['gene_name'] = filtered_gene_counts.index
    filtered_gene_counts['gene_id'] = filtered_gene_counts['gene_name'].apply(lambda x: commited_genes[x])

    def add_gene_counts_to_file(col, filtered_gene_counts, sample_id):
        tmp_cov_df = filtered_gene_counts[[col, 'gene_id']].copy()
        tmp_cov_df['rpkm'] = tmp_cov_df[col]
        tmp_cov_df['sample_id'] = sample_id
        with open(args.tmp_file, 'w') as gene_counts_file:
            tmp_cov_df[['gene_id', 'sample_id', 'rpkm']].to_csv(gene_counts_file, index=False, header=False)

    for i, col in enumerate(val_cols):
        logging.info("Saving gene counts to file for {}. ({}/{})".format(col, i+1, nr_columns))
        sample = all_samples[col]
        add_gene_counts_to_file(col, filtered_gene_counts, sample.id)
        session.execute("COPY gene_count (gene_id, sample_id, rpkm) FROM '{}' WITH CSV;".format(args.tmp_file))

    logging.info("{} out of {} are annotated genes".format(len(filtered_gene_counts), total_gene_count_len))
    session.commit()

    logging.info("Refreshing materialized view")
    refresh_all_mat_views()
    session.commit()
    logging.info("Finished!")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample_info", help="A csv file with all the sample information.")
    parser.add_argument("--all_annotations", help=("A tsv file with all the possible annotations."
            "The three columns should be ['type_id', 'gene_id', 'description']"))
    parser.add_argument("--annotation_source_info", help="A csv file with all the annotation source info.")
    parser.add_argument("--gene_annotations_cog", help="A tsv file with all the gene annotations")
    parser.add_argument("--gene_annotations_pfam", help="A tsv file with all the pfam gene annotations")
    parser.add_argument("--gene_annotations_tigrfam", help="A tsv file with all the tigrfam gene annotations")
    parser.add_argument("--reference_assembly", help="Name of the reference assembly that the genes belong to")
    parser.add_argument("--gene_counts", help="A tsv file with each sample as a column containing all the gene counts")
    parser.add_argument("--taxonomy_per_gene", help="A tsv file with taxonomic annotation per gene")
    parser.add_argument("--metadata_reference", help="A tsv file with which metadata parameters that are supposed to be added")
    parser.add_argument("--tmp_file", help="A file that will be used to import gene counts to postgres")
    args = parser.parse_args()

    main(args)
