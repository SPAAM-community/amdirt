from sys import path
import os
from amdirt.core import (
    prepare_accession_table,
    prepare_bibtex_file,
    prepare_eager_table,
    prepare_mag_table,
    prepare_aMeta_table,
    is_merge_size_zero,
    prepare_taxprofiler_table,
    get_libraries,
    get_remote_resources,
    get_json_path,
)
from amdirt.validate import AMDirValidator
from amdirt.validate.exceptions import DatasetValidationError
from json import load
from amdirt.core import logger
import pandas as pd
import warnings


def run_convert(
    samples,
    libraries,
    table_name,
    tables=None,
    output=".",
    bibliography=False,
    librarymetadata=False,
    curl=False,
    aspera=False,
    eager=False,
    fetchngs=False,
    sratoolkit=False,
    ameta=False,
    taxprofiler=False,
    mag=False,
    verbose=False,
):
    """Run the amdirt conversion application to input samplesheet tables for different pipelines

    Args:
        samples (str): Path to AncientMetagenomeDir filtered samples tsv file
        libraries(str): Optional path to AncientMetagenomeDir pre-filtered libraries tsv file
        table_name (str): Name of the table of the table to convert
        tables (str): Path to JSON file listing tables
        output (str): Path to output table. Defaults to "."
    """
    os.makedirs(output, exist_ok=True)

    if not verbose:
        warnings.filterwarnings("ignore")
    supported_archives = ["ENA", "SRA"]

    # Validate input table
    if tables is None:
        remote_resources = get_remote_resources()
    else:
        with open(tables, "r") as f:
            remote_resources = load(f)

    if table_name not in remote_resources["samples"]:
        raise ValueError(f"{table_name} not found in AncientMetagenomeDir file")
    if not verbose:
        warnings.filterwarnings("ignore")

    schema = remote_resources[f"samples_schema"][table_name]
    dataset_valid = list()
    v = AMDirValidator(schema, samples)
    dataset_valid.append(v.parsing_ok)
    if v.parsing_ok:
        dataset_valid.append(v.validate_schema())
        dataset_valid.append(v.check_duplicate_rows())
        dataset_valid.append(v.check_columns())

    dataset_valid = all(dataset_valid)
    if dataset_valid is False:
        v.to_rich()
        raise DatasetValidationError("Input sample dataset is not valid")
    else:
        logger.info("Input sample dataset is valid")
        samples = pd.read_csv(samples, sep="\t")
        remote_libraries = pd.read_csv(
            remote_resources["libraries"][table_name], sep="\t"
        )

    if not libraries:
        selected_libraries = get_libraries(
            samples=samples,
            libraries=remote_libraries,
            table_name=table_name,
            supported_archives=supported_archives,
        )
    else:
        schema = remote_resources[f"libraries_schema"][table_name]
        dataset_valid = list()
        v = AMDirValidator(schema, libraries)
        dataset_valid.append(v.parsing_ok)
        if v.parsing_ok:
            dataset_valid.append(v.validate_schema())
            dataset_valid.append(v.check_duplicate_rows())
            dataset_valid.append(v.check_columns())

        dataset_valid = all(dataset_valid)
        if dataset_valid is False:
            v.to_rich()
            raise DatasetValidationError("Input libraries dataset is not valid")
        else:
            logger.info("Input libraries dataset is valid")
            libraries = pd.read_csv(libraries, sep="\t")
            selected_libraries = get_libraries(
                samples=samples,
                libraries=libraries,
                table_name=table_name,
                supported_archives=supported_archives,
            )

    accession_table = prepare_accession_table(
        samples=samples,
        libraries=selected_libraries,
        table_name=table_name,
        supported_archives=supported_archives,
    )

    logger.warning(
        "We provide no warranty to the accuracy of the generated input sheets."
    )

    if bibliography == True:
        bibfile = f"{output}/AncientMetagenomeDir_bibliography.bib"
        logger.info(f"Writing Bibtex citation file to {bibfile}")
        with open(bibfile, "w") as fw:
            fw.write(prepare_bibtex_file(samples))

    if table_name in ["ancientmetagenome-environmental"]:
        col_drop = ["archive_accession"]
    else:
        col_drop = ["archive_accession", "sample_host"]

    if librarymetadata == True:
        tbl_file = f"{output}/AncientMetagenomeDir_filtered_libraries.tsv"
        logger.info(f"Writing filtered libraries table to {tbl_file}")
        librarymetadata = selected_libraries.drop(col_drop, axis=1)
        librarymetadata.to_csv(
            tbl_file,
            sep="\t",
            index=False,
        )

    if curl == True:
        dl_file = f"{output}/AncientMetagenomeDir_curl_download_script.sh"
        logger.info(f"Writing curl download script to {dl_file}")
        with open(dl_file, "w") as fw:
            fw.write(accession_table["curl_script"])

    if aspera == True:
        dl_file = f"{output}/AncientMetagenomeDir_aspera_download_script.sh"
        logger.info(f"Writing Aspera download script to {dl_file}")
        logger.warning(
            "You will need to set the ${ASPERA_PATH} environment variable. See https://amdirt.readthedocs.io for more information."
        )
        with open(dl_file, "w") as fw:
            fw.write(accession_table["aspera_script"])

    if fetchngs == True:
        dl_file = f"{output}/AncientMetagenomeDir_nf_core_fetchngs_download_script.sh"
        logger.info(f"Writing nf-core/fetchngs table to {dl_file}")
        accession_table["df"]["archive_data_accession"].to_csv(
            dl_file,
            sep="\t",
            header=False,
            index=False,
        )
    if sratoolkit == True:
        dl_file = f"{output}/AncientMetagenomeDir_sratoolkit_download_script.sh"
        logger.info(f"Writing sratoolkit/fasterq-dump download script to {dl_file}")
        with open(dl_file, "w") as fw:
            fw.write(accession_table["fasterq_dump_script"])

    if eager == True:
        tbl_file = f"{output}/AncientMetagenomeDir_nf_core_eager_input_table.tsv"
        logger.info(f"Writing nf-core/eager table to {tbl_file}")
        eager_table = prepare_eager_table(
            samples=samples,
            libraries=selected_libraries,
            table_name=table_name,
            supported_archives=supported_archives,
        )
        eager_table.to_csv(
            tbl_file,
            sep="\t",
            index=False,
        )

    if taxprofiler == True:
        tbl_file = f"{output}/AncientMetagenomeDir_nf_core_taxprofiler_input_table.csv"
        logger.info(f"Writing nf-core/taxprofiler table to {tbl_file}")
        taxprofiler_table = prepare_taxprofiler_table(
            samples=samples,
            libraries=selected_libraries,
            table_name=table_name,
            supported_archives=supported_archives,
        )
        taxprofiler_table.to_csv(
            tbl_file,
            header=False,
            index=False,
        )

    if ameta == True:
        tbl_file = f"{output}/AncientMetagenomeDir_aMeta_input_table.tsv"
        logger.info(f"Writing aMeta table to {tbl_file}")
        logger.warning(
            "aMeta does not support pairs. You must manually merge pair-end data before using samplesheet."
        )
        aMeta_table = prepare_aMeta_table(
            samples=samples,
            libraries=selected_libraries,
            table_name=table_name,
            supported_archives=supported_archives,
        )

        aMeta_table.to_csv(
            tbl_file,
            sep="\t",
            index=False,
        )

    if mag == True:
        logger.info("Preparing nf-core/mag table(s)")
        mag_table_single, mag_table_paired = prepare_mag_table(
            samples=samples,
            libraries=selected_libraries,
            table_name=table_name,
            supported_archives=supported_archives,
        )
        if not mag_table_single.empty:
            mag_tbl_single_file = (
                f"{output}/AncientMetagenomeDir_nf_core_mag_input_single_table.csv"
            )
            logger.info(
                f"Writing nf-core/mag single-end table to {mag_tbl_single_file}"
            )
            mag_table_single.to_csv(
                mag_tbl_single_file,
                index=False,
            )
        if not mag_table_paired.empty:
            mag_tbl_paired_file = (
                f"{output}/AncientMetagenomeDir_nf_core_mag_input_paired_table.csv"
            )
            logger.info(
                f"Writing nf-core/mag paired-end table to {mag_tbl_paired_file}"
            )
            mag_table_paired.to_csv(
                mag_tbl_paired_file,
                index=False,
            )
