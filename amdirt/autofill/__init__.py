from amdirt.validate.domain import DatasetValidator
from amdirt.core import get_json_path, logger
from amdirt.core.ena import ENAPortalAPI
from amdirt.validate.exceptions import NetworkError
import json

import sys
import pandas as pd

def run_autofill(accession, table_name=None, schema=None, dataset=None, sample_output=None, library_output=None, verbose=False, output_ena_table=None):
    """Autofill the metadata of a table from ENA

    Args:
        accession (tuple(str)): ENA project accession. Multiple accessions can be space separated (e.g. PRJNA123 PRJNA456)
        table_name (str): Name of the table to be filled
        schema (str): Path to the schema file
        dataset (str): Path to the dataset file
        sample_output (str): Path to the sample output table file
        library_output (str): Path to the library output table file

    Returns:
        pd.DataFrame: ENA metadata run level table
    """

    if schema is None and dataset is None:
        json_conf = get_json_path()
        with open(json_conf) as c:
            tables = json.load(c)
            samples = tables["samples"]
            samples_schema = tables["samples_schema"]
            libraries = tables["libraries"]
            libraries_schema = tables["libraries_schema"]
        if table_name not in samples:
            raise Exception("Table name not found in AncientMetagenomeDir file")
    else:
        logger.error("Not implemented yet")

    sample = DatasetValidator(
        schema=samples_schema[table_name], dataset=samples[table_name]
    )
    libraries = DatasetValidator(
        schema=libraries_schema[table_name], dataset=libraries[table_name]
    )

    libraries.to_rich()

    sample_df = sample.dataset.iloc[:0, :].copy()
    libraries_df = libraries.dataset.iloc[:0, :].copy()

    ena = ENAPortalAPI()
    if ena.status():
        logger.info("ENA API is up")
    else:
        raise NetworkError("ENA API is unreachable")
    
    query_dict = list()
    for a in accession:
        query_res = ena.query(a, fields=[
            "experiment_accession",
            "study_accession",
            "run_accession",
            "sample_alias",
            "sample_accession",
            "secondary_sample_accession",            
            "nominal_length",
            "scientific_name",
            "sample_title",
            "bam_ftp",
            "sra_ftp",
            "fastq_ftp",
            "fastq_md5",
            "fastq_bytes",
            "read_count",
            "submitted_ftp",
            "submitted_aspera",
            "submitted_format",
            "instrument_platform",
            "instrument_model",
            "scientific_name",
            "tax_id",
            "library_name",
            "library_layout",
            "library_strategy",
            "library_selection",
            "library_source",
        ])
        query_dict += query_res
    df_out = pd.DataFrame.from_dict(query_dict)
    
    # Output ENA table to .csv.gz file
    if output_ena_table is not None:
        ena_table_output_path = output_ena_table + '.tsv.gz'
        logger.info(f"ENA Table head (First 5 lines + headers)")
        print(df_out.head(5))
        df_out.to_csv(ena_table_output_path, sep='\t', index=False, compression='gzip')
        logger.info(f"Saved ENA table to {ena_table_output_path}")
        
    df_out.rename(
        columns={
            "study_accession": "archive_project",
            "run_accession":"archive_data_accession",
            "secondary_sample_accession": "archive_sample_accession",
            "sample_alias": "sample_name",
            "fastq_ftp": "download_links",
            "fastq_md5": "download_md5s",
            "fastq_bytes": "download_sizes"
        },
        inplace=True
        )
    
    # sample table
    sample_out = df_out.copy(deep=True)
    sample_out.rename(
        columns={
            "archive_sample_accession": "archive_accession",
        },
        inplace=True
    )
    for col in sample_df.columns:
        if col not in sample_out.columns:
            sample_out[col] = None
    sample_out = sample_out[sample_df.columns]
    sample_out = sample_out.loc[:,~sample_out.columns.duplicated()].copy()
    sample_out = sample_out.drop_duplicates(subset=["archive_accession"])
    sample_out = sample_out.astype(sample_df.dtypes.to_dict())

    # library table
    lib_out = df_out.copy(deep=True)
    for col in libraries_df.columns:
        if col not in lib_out.columns:
            lib_out[col] = None
    lib_out = lib_out[libraries_df.columns]
    lib_out = lib_out.loc[:,~lib_out.columns.duplicated()].copy()
    lib_out['read_count'] = lib_out['read_count'].str.replace(",", "",
                                                              regex=False)
    lib_out = lib_out.astype(libraries_df.dtypes.to_dict())

    if library_output:
        logger.info(f"Found {lib_out.shape[0]} libraries")
        logger.info(f"Writing libraries metadata to {library_output}")
        lib_out.to_csv(library_output, index=False, sep="\t")
    if sample_output:
        logger.info(f"Found {sample_out.shape[0]} samples")
        logger.info(f"Writing samples metadata to {sample_output}")
        logger.warning("Sample name must match that reported in publication and/or sample-level table. ENA reported sample-name may not be correct! Check before submission.")
        sample_out.to_csv(sample_output, index=False, sep="\t")
