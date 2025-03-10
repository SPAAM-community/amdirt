from amdirt.core import (
    logger,
    get_amdir_tags,
    get_remote_resources,
    check_allowed_values,
)
import requests


def download(table: str, table_type: str, release: str, output: str = ".") -> str:
    """
    Download a table from the amdirt repository.

    Parameters
    ----------
    table : str
        The AncientMetagenomeDir table to download.
    table_type : str
        The type of table to download. Allowed values are ['samples', 'libraries'].
    release : str
        The release of the table to download. Must be a valid release tag.
    output: str
        The output directory to save the table. Default is the current directory.

    Returns
    -------
    str:
        The path to the downloaded table.

    Raises
    ------
    ValueError
        If an invalid table is provided.
    ValueError
        If an invalid table type is provided.
    ValueError
        If an invalid release is provided.
    """

    resources = get_remote_resources()
    tags = get_amdir_tags()
    if tags != ["master"]:
        if check_allowed_values(tags, release) is False:
            raise ValueError(f"Invalid release: {release}. Allowed values are {tags}")

    tables = resources["samples"]
    if check_allowed_values(tables, table) is False:
        raise ValueError(f"Invalid table: {table}. Allowed values are {tables}")

    if check_allowed_values(["samples", "libraries"], table_type) is False:
        raise ValueError(
            f"Invalid table type: {table_type}. Allowed values are ['samples', 'libraries']"
        )
    table_filename = f"{table}_{table_type}_{release}.tsv"
    logger.info(
        f"Downloading {table} {table_type} table from {release} release, saving to {output}/{table_filename}"
    )
    t = requests.get(resources[table_type][table].replace("master", release))
    with open(table_filename, "w") as fh:
        fh.write(t.text)

    return table_filename
