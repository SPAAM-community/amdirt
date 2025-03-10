from amdirt.validate.application import AMDirValidator
from amdirt.validate.exceptions import DatasetValidationError
import warnings
import pandas as pd
from amdirt.core import logger, get_remote_resources
from os.path import join


def merge_new_df(
    dataset,
    table_type,
    table_name,
    markdown,
    outdir,
    verbose,
    schema_check=True,
    line_dup=True,
    columns=True,
):
    """Merge a new dataset with the remote master dataset

    Args:
        dataset (Path): Path to new dataset
        table_type (str): Type of table to merge (samples or libraries)
        table_name (str): Kind of table to merge (e.g. ancientmetagenome-hostassociated, ancientmetagenome-environmental, etc.)
        markdown (bool): Log in markdown format
        outdir (Path): Path to output directory
        verbose (bool): Enable verbose mode
        schema_check (bool, optional): Enable schema check. Defaults to True.
        line_dup (bool, optional): Enable line duplication check. Defaults to True.
        columns (bool, optional): Enable columns presence/absence check. Defaults to True.

    Raises:
        ValueError: Table type must be either 'samples' or 'libraries'
        ValueError: Table name not found in AncientMetagenomeDir file
        DatasetValidationError: New dataset is not valid
    """
    remote_resources = get_remote_resources()

    if table_type not in ["samples", "libraries"]:
        raise ValueError("table_type must be either 'samples' or 'libraries'")
    if table_name not in remote_resources[table_type]:
        raise ValueError("table_name not found in AncientMetagenomeDir file")
    if not verbose:
        warnings.filterwarnings("ignore")

    schema = remote_resources[f"{table_type}_schema"][table_name]
    dataset_valid = list()
    v = AMDirValidator(schema, dataset)
    dataset_valid.append(v.parsing_ok)
    if schema_check and v.parsing_ok:
        dataset_valid.append(v.validate_schema())
    if line_dup and v.parsing_ok:
        dataset_valid.append(v.check_duplicate_rows())
    if columns and v.parsing_ok:
        dataset_valid.append(v.check_columns())

    dataset_valid = all(dataset_valid)
    if dataset_valid is False:
        if markdown:
            v.to_markdown()
        else:
            v.to_rich()
        raise DatasetValidationError("New Dataset is not valid")

    else:
        remote_dataset = pd.read_table(
            remote_resources[table_type][table_name], dtype=dict(v.dataset.dtypes)
        )

        logger.info("New Dataset is valid")
        logger.info(
            f"Merging new dataset with remote {table_name} {table_type} dataset"
        )
        dataset = pd.concat([remote_dataset, v.dataset])
        dataset.drop_duplicates(inplace=True)
        dataset.to_csv(
            join(outdir, f"{table_name}_{table_type}.tsv"),
            sep="\t",
            na_rep="NA",
            index=False,
        )
        logger.info(
            f"New {table_name} {table_type} dataset written to {join(outdir,f'{table_name}_{table_type}.tsv')}"
        )
