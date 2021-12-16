from os import path
import requests
import xmltodict
from numpy import where
import pandas as pd

pd.options.mode.chained_assignment = None


def get_colour_chemistry(instrument):
    """
    Get number of colours used in sequencing chemistry
    Args:
        instrument(str): Name of the instrument
    Returns:
        int: number of colours used in sequencing chemistry
    """
    chemistry_colours = {
        "bgiseq": 4,
        "miseq": 4,
        "hiseq": 4,
        "genome analyzer": 4,
        "nextseq": 2,
        "novaseq": 2,
    }

    for k in chemistry_colours:
        if k in instrument.lower():
            return chemistry_colours[k]


def get_experiment_accession(run_accession):
    resp = requests.get(f"https://www.ebi.ac.uk/ena/browser/api/xml/{run_accession}")
    tree = xmltodict.parse(resp.content.decode())
    print(run_accession)
    return tree["RUN_SET"]["RUN"]["EXPERIMENT_REF"]["@accession"]


def get_filename(path_string, prepend_exp=False):
    """
    Get Fastq Filename from download_links column

    Args:
        path_string(str): path to fastq files urls, comma separated
        orientation(str): [fwd | rev]
        prepend_exp(bool): prepend experiment accession number
    Returns
        str: name of Fastq file
    """

    try:
        path_string = str(path_string)
        if path_string == "nan":
            return "NA"
        fwd, rev = path_string.split(";")
        fwd = fwd.split("/")[-1]
        rev = rev.split("/")[-1]
    except (ValueError, AttributeError):
        fwd = path_string
        fwd = fwd.split("/")[-1]
    if prepend_exp:
        run_accession = fwd.split(".")[0].split("_")[0]
        # print(run_accession)
        exp_accession = get_experiment_accession(run_accession)
    try:
        if prepend_exp:
            fwd = f"{exp_accession}_{fwd}"
            rev = f"{exp_accession}_{rev}"
        return fwd, rev
    except UnboundLocalError:
        return fwd, "NA"


def prepare_eager_table(samples, libraries):
    """Prepare nf-core/eager tsv input table

    Args:
        sample (pd.dataFrame): selected samples table
        library (pd.dataFrame): library table
    """

    stacked_samples = (
        samples["archive_accession"]
        .str.split(",", expand=True)
        .stack()
        .reset_index(level=0)
        .set_index("level_0")
        .rename(columns={0: "archive_accession"})
        .join(samples.drop("archive_accession", axis=1))
    )

    libraries = libraries.merge(
        stacked_samples[["archive_accession", "sample_host"]],
        left_on="archive_sample_accession",
        right_on="archive_accession",
    )
    select_libs = list(stacked_samples["archive_accession"])
    selected_libraries = libraries.query("archive_sample_accession in @select_libs")

    selected_libraries["Colour_Chemistry"] = selected_libraries[
        "instrument_model"
    ].apply(get_colour_chemistry)

    selected_libraries[
        "UDG_Treatment"
    ] = selected_libraries.library_treatment.str.split("-", expand=True)[0]

    selected_libraries["download_links"].apply(get_filename, prepend_exp=True)

    selected_libraries["R1"], selected_libraries["R2"] = zip(
        *selected_libraries["download_links"].apply(get_filename, prepend_exp=True)
    )
    selected_libraries["Lane"] = 0
    selected_libraries["SeqType"] = where(
        selected_libraries["library_layout"] == "SINGLE", "SE", "PE"
    )
    selected_libraries["BAM"] = "NA"
    print(selected_libraries.columns)
    col2keep = [
        "sample_name",
        "archive_run_accession",
        "Lane",
        "Colour_Chemistry",
        "SeqType",
        "sample_host",
        "strand_type",
        "UDG_Treatment",
        "R1",
        "R2",
        "BAM",
    ]
    selected_libraries = selected_libraries[col2keep].rename(
        columns={
            "sample_name": "Sample_Name",
            "archive_run_accession": "Library_ID",
            "sample_host": "Organism",
            "strand_type": "Strandedness",
        }
    )

    return selected_libraries


def prepare_accession_table(samples, libraries):
    """Get accession lists for samples and libraries

    Args:
        samples (pd.dataFrame): selected samples table
        libraries (pd.dataFrame): library table
    """

    stacked_samples = (
        samples["archive_accession"]
        .str.split(",", expand=True)
        .stack()
        .reset_index(level=0)
        .set_index("level_0")
        .rename(columns={0: "archive_accession"})
        .join(samples.drop("archive_accession", axis=1))
    )

    libraries = libraries.merge(
        stacked_samples[["archive_accession", "sample_host"]],
        left_on="archive_sample_accession",
        right_on="archive_accession",
    )
    select_libs = list(stacked_samples["archive_accession"])
    selected_libraries = libraries.query("archive_sample_accession in @select_libs")

    return selected_libraries["archive_accession"].to_frame()