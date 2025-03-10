from typing import Tuple, Iterable
from pathlib import Path
import requests
from numpy import where
import pandas as pd
import streamlit as st
from packaging import version
from packaging.version import InvalidVersion
from importlib.resources import files as get_module_dir
import os
import logging
import colorlog
from json import load


pd.options.mode.chained_assignment = None

logging.basicConfig(level=logging.INFO)

handler = colorlog.StreamHandler()
handler.setFormatter(
    colorlog.ColoredFormatter("%(log_color)s%(name)s [%(levelname)s]: %(message)s")
)

logger = colorlog.getLogger("amdirt")
logger.addHandler(handler)
logger.propagate = False


def monkeypatch_get_storage_manager():
    if st.runtime.exists():
        return st.runtime.get_instance().cache_storage_manager
    else:
        # When running in "raw mode", we can't access the CacheStorageManager,
        # so we're falling back to InMemoryCache.
        # https://github.com/streamlit/streamlit/issues/6620
        # _LOGGER.warning("No runtime found, using MemoryCacheStorageManager")
        return (
            st.runtime.caching.storage.dummy_cache_storage.MemoryCacheStorageManager()
        )


st.runtime.caching._data_caches.get_storage_manager = monkeypatch_get_storage_manager


def get_json_path():
    path = get_module_dir("amdirt.assets").joinpath("tables.json")
    return path


def get_remote_resources():
    json_path = get_json_path()
    with open(json_path, "r") as f:
        return load(f)


@st.cache_data
def get_amdir_tags():
    r = requests.get(
        "https://api.github.com/repos/SPAAM-community/AncientMetagenomeDir/tags"
    )
    if r.status_code == 200:
        tags = [
            tag['name']
            for tag in r.json()
            if tag['name'] != 'latest'
        ]
        return [
            tag
            for tag in tags
            if version.parse(tag) >= version.parse("v22.09")
        ]
    else:
        logger.warning(
            "Could not fetch tags from AncientMetagenomeDir. Defaulting to master. Metadata may not yet be officially released."
        )
        return ["master"]


@st.cache_data
def get_latest_tag(tags):
    try:
        return sorted(tags, key=lambda x: version.Version(x))[-1]
    except InvalidVersion:
        if "master" in tags:
            return "master"
        else:
            raise InvalidVersion("No valid tags found")


def check_allowed_values(ref: list, test: str):
    """
    Check if test is in ref
    Args:
        ref(list): List of allowed values
        test(str): value to check
    """

    if test in ref:
        return True
    return False


def get_colour_chemistry(instrument: str) -> int:
    """
    Get number of colours used in sequencing chemistry. If the instrument is
    not a known Illumina sequencer with two-dye chemistry, a colour chemistry
    of four dyes is assumed. 

    Args:
        instrument(str): Name of the instrument
    Returns:
        int: number of colours used in sequencing chemistry
    """
    instruments_2dye = [
        "Illumina MiniSeq",
        "Illumina NovaSeq 6000",
        "Illumina NovaSeq X",
        "Illumina iSeq 100",
        "NextSeq 1000",
        "NextSeq 2000",
        "NextSeq 500",
        "NextSeq 550",
    ]
    if instrument in instruments_2dye:
        return 2
    else:
        return 4


def doi2bib(doi: str) -> str:
    """
    Return a bibTeX string of metadata for a given DOI.
    """

    url = "http://doi.org/" + doi

    headers = {"accept": "application/x-bibtex"}
    r = requests.get(url, headers=headers)

    return r.text


@st.cache_data
def get_libraries(
    table_name: str,
    samples: pd.DataFrame,
    libraries: pd.DataFrame,
    supported_archives: Iterable[str],
):
    """Get filtered libraries from samples and libraries tables

    Args:
        table_name (str): Name of the table of the table to convert
        samples (pd.DataFrame): Sample table
        libraries (pd.DataFrame): Library table
        supported_archives (Iterable[str]): Supported archives list

    Returns:
        pd.DataFrame: filtered libraries table
    """
    stacked_samples = (
        samples.query("archive in @supported_archives")
        .loc[:, "archive_accession"]
        .str.split(",", expand=True)
        .stack()
        .reset_index(level=0)
        .set_index("level_0")
        .rename(columns={0: "archive_accession"})
        .join(samples.drop("archive_accession", axis=1))
    )

    if table_name in [
        "ancientmetagenome-environmental",
    ]:
        sel_col = ["archive_accession"]
    else:
        sel_col = ["archive_accession", "sample_host"]
    libraries = libraries.merge(
        stacked_samples[sel_col],
        left_on="archive_sample_accession",
        right_on="archive_accession",
    )
    select_libs = list(stacked_samples["archive_accession"])
    selected_libraries = libraries.query("archive_sample_accession in @select_libs")

    return selected_libraries


def get_filename(path_string: str, orientation: str) -> Tuple[str, str]:
    """
    Get Fastq Filename from download_links column

    Args:
        path_string(str): path to fastq files urls, comma separated
        orientation(str): [fwd | rev]
    Returns
        str: name of Fastq file
    """

    if ";" in path_string:
        fwd = Path(path_string.split(";")[0]).name
        rev = Path(path_string.split(";")[1]).name
    else:
        fwd = Path(path_string).name
        rev = "NA"
    if orientation == "fwd":
        return fwd
    elif orientation == "rev":
        return rev


def parse_to_mag(libraries):
    libraries["short_reads_1"] = libraries["download_links"].apply(
        get_filename, orientation="fwd"
    )
    libraries["short_reads_2"] = libraries["download_links"].apply(
        get_filename, orientation="rev"
    )
    libraries["short_reads_2"] = libraries["short_reads_2"].replace("NA", "")
    libraries["longs_reads"] = ""
    col2keep = [
        "archive_data_accession",
        "archive_sample_accession",
        "short_reads_1",
        "short_reads_2",
        "longs_reads",
    ]
    libraries = libraries[col2keep].rename(
        columns={
            "archive_data_accession": "sample",
            "archive_sample_accession": "group",
        }
    )
    return libraries


@st.cache_data
def prepare_eager_table(
    samples: pd.DataFrame,
    libraries: pd.DataFrame,
    table_name: str,
    supported_archives: Iterable[str],
) -> pd.DataFrame:
    """Prepare nf-core/eager tsv input table

    Args:
        sample (pd.dataFrame): selected samples table
        library (pd.dataFrame): library table
        table_name (str): Name of the table
        supported_archives (list): list of supported archives
    """

    ## Reduce risk of filename incompatible characters in sample names
    libraries["sample_name"] = libraries["sample_name"].str.replace(" ", "_").replace("/", "_")

    libraries["Colour_Chemistry"] = libraries["instrument_model"].apply(
        get_colour_chemistry
    )

    libraries["UDG_Treatment"] = libraries.library_treatment.str.split(
        "-", expand=True
    )[0]

    libraries["R1"] = libraries["download_links"].apply(get_filename, orientation="fwd")

    libraries["R2"] = libraries["download_links"].apply(get_filename, orientation="rev")

    libraries["Lane"] = 0
    libraries["SeqType"] = where(libraries["library_layout"] == "SINGLE", "SE", "PE")
    libraries["BAM"] = "NA"
    if table_name == "ancientmetagenome-environmental":
        libraries["sample_host"] = "environmental"
    col2keep = [
        "sample_name",
        "archive_data_accession",
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
    libraries = libraries[col2keep].rename(
        columns={
            "sample_name": "Sample_Name",
            "archive_data_accession": "Library_ID",
            "sample_host": "Organism",
            "strand_type": "Strandedness",
        }
    )

    return libraries


@st.cache_data
def prepare_mag_table(
    samples: pd.DataFrame,
    libraries: pd.DataFrame,
    table_name: str,
    supported_archives: Iterable[str],
) -> pd.DataFrame:
    """Prepare nf-core/mag tsv input table

    Args:
        sample (pd.dataFrame): selected samples table
        library (pd.dataFrame): library table
        table_name (str): Name of the table
        supported_archives (list): list of supported archives
    """

    ## Reduce risk of filename incompatible characters in sample names
    libraries["sample_name"] = libraries["sample_name"].str.replace(" ", "_").replace("/", "_")

    # Create a DataFrame for "SINGLE" values
    single_libraries = libraries[libraries["library_layout"] == "SINGLE"]

    # Create a DataFrame for "PAIRED" values
    paired_libraries = libraries[libraries["library_layout"] == "PAIRED"]

    if not single_libraries.empty:
        single_libraries = parse_to_mag(single_libraries)
    if not paired_libraries.empty:
        paired_libraries = parse_to_mag(paired_libraries)

    return single_libraries, paired_libraries


@st.cache_data
def prepare_accession_table(
    samples: pd.DataFrame,
    libraries: pd.DataFrame,
    table_name: str,
    supported_archives: Iterable[str],
) -> pd.DataFrame:
    """Get accession lists for samples and libraries

    Args:
        samples (pd.dataFrame): selected samples table
        libraries (pd.dataFrame): library table
        table_name (str): Name of the table
        supported_archives (list): list of supported archives
    """

    # libraries = get_libraries(
    #     table_name=table_name,
    #     samples=samples,
    #     libraries=libraries,
    #     supported_archives=supported_archives,
    # )

    
    # Downloading with curl or aspera instead of fetchngs
    urls = []
    accessions = set(libraries["archive_data_accession"])
    links = set()
    
    for iter, row in libraries.iterrows():
        urls.append((row["download_links"], row["download_md5s"]))
    
    for u in urls:
        l = u[0].split(";")
        m = u[1].split(";")
        
        for i in range(len(l)):
            links.add((l[i], m[i]))
    
    links = set(links)
    
    dl_script_header = "#!/usr/bin/env bash\n"
    curl_script = (
        "\n".join([f"curl -L ftp://{l[0]} -o {l[0].split('/')[-1]} && md5sum {l[0].split('/')[-1]} && md5sum {l[0].split('/')[-1]} | awk '{{print $1}}' | grep -q ^{l[1]}$ || echo -e \"\\e[31mMD5 hash do not match for {l[0].split('/')[-1]}. Expected hash: {l[1]}\\e[0m\"" for l in links]) + "\n"
    )
    aspera_script = (
        "\n".join(
            [
                "ascp -QT -l 300m -P 33001 "
                "-i ${ASPERA_PATH}/etc/asperaweb_id_dsa.openssh "
                f"era-fasp@fasp.sra.ebi.ac.uk:{'/'.join(l[0].split('/')[1:])} ."
                for l in links
            ]
        )
        + "\n"
    )
    fasterq_dump_script = (
        "\n".join([f"fasterq-dump --split-files -p {a}" for a in accessions]) + "\n"
    )

    return {
        "df": libraries[["archive_data_accession", "download_sizes"]].drop_duplicates(),
        "curl_script": dl_script_header + curl_script,
        "aspera_script": dl_script_header + aspera_script,
        "fasterq_dump_script": dl_script_header + fasterq_dump_script,
    }


@st.cache_data
def prepare_taxprofiler_table(
    samples: pd.DataFrame,
    libraries: pd.DataFrame,
    table_name: str,
    supported_archives: Iterable[str],
) -> pd.DataFrame:
    """Prepare taxprofiler csv input table

    Args:
        sample (pd.dataFrame): selected samples table
        library (pd.dataFrame): library table
        table_name (str): Name of the table
        supported_archives (list): list of supported archives
    """

    ## Reduce risk of filename incompatible characters in sample names
    libraries["sample_name"] = libraries["sample_name"].str.replace(" ", "_").replace("/", "_")

    libraries["fastq_1"] = libraries["download_links"].apply(
        get_filename, orientation="fwd"
    )

    libraries["fastq_2"] = libraries["download_links"].apply(
        get_filename, orientation="rev"
    )

    libraries["fastq_2"] = libraries["fastq_2"].replace("NA", "")

    libraries["fasta"] = ""

    libraries["instrument_model"] = where(
        libraries["instrument_model"]
        .str.lower()
        .str.contains("illumina|nextseq|hiseq|miseq"),
        "ILLUMINA",
        where(
            libraries["instrument_model"].str.lower().str.contains("torrent"),
            "ION_TORRENT",
            where(
                libraries["instrument_model"].str.lower().str.contains("helicos"),
                "HELICOS",
                where(
                    libraries["instrument_model"].str.lower().str.contains("bgiseq"),
                    "BGISEQ",
                    where(
                        libraries["instrument_model"].str.lower().str.contains("454"),
                        "LS454",
                        libraries["instrument_model"],
                    ),
                ),
            ),
        ),
    )

    col2keep = [
        "sample_name",
        "library_name",
        "instrument_model",
        "fastq_1",
        "fastq_2",
        "fasta",
    ]
    libraries = libraries[col2keep].rename(
        columns={
            "sample_name": "sample",
            "library_name": "run_accession",
            "instrument_model": "instrument_platform",
        }
    )

    return libraries


@st.cache_data
def prepare_aMeta_table(
    samples: pd.DataFrame,
    libraries: pd.DataFrame,
    table_name: str,
    supported_archives: Iterable[str],
) -> pd.DataFrame:
    """Prepare aMeta tsv input table

    Args:
        sample (pd.dataFrame): selected samples table
        library (pd.dataFrame): library table
        table_name (str): Name of the table
        supported_archives (list): list of supported archives
    """

    ## Reduce risk of filename incompatible characters in sample names
    libraries["sample_name"] = libraries["sample_name"].replace(" ", "_").replace("/", "_")

    libraries["Colour_Chemistry"] = libraries["instrument_model"].apply(
        get_colour_chemistry
    )

    libraries["UDG_Treatment"] = libraries.library_treatment.str.split(
        "-", expand=True
    )[0]

    libraries["R1"] = libraries["download_links"].apply(get_filename, orientation="fwd")

    libraries["R2"] = libraries["download_links"].apply(get_filename, orientation="rev")

    libraries["Lane"] = 0
    libraries["SeqType"] = where(libraries["library_layout"] == "SINGLE", "SE", "PE")
    libraries["BAM"] = "NA"
    if table_name == "ancientmetagenome-environmental":
        libraries["sample_host"] = "environmental"
    col2keep = ["archive_data_accession", "R1"]
    libraries = libraries[col2keep].rename(
        columns={
            "archive_data_accession": "sample",
            "R1": "fastq",
        }
    )

    return libraries


@st.cache_data
def prepare_bibtex_file(samples: pd.DataFrame) -> str:
    dois = set()
    failed_dois = set()
    dois_set = set(list(samples["publication_doi"]))
    dois_set.add("10.1038/s41597-021-00816-y")
    for doi in dois_set:
        try:
            bibtex_str = doi2bib(doi)
            if len(bibtex_str) == 0:
                failed_dois.add(doi)
            else:
                dois.add(bibtex_str)
        except Exception as e:
            logger.info(e)
            pass
    # Print warning for DOIs that do not have an entry
    if len(failed_dois) > 0:
        st.warning(
            "Citation information could not be resolved for the "
            "following DOIs: " + ", ".join(failed_dois) + ". Please "
            "check how to cite these publications manually!"
        )
        logger.warning(
            "Citation information could not be resolved for the "
            "following DOIs: " + ", ".join(failed_dois) + ". Please "
            "check how to cite these publications manually!"
        )

    dois_string = "\n".join(list(dois))
    return dois_string


def is_merge_size_zero(
    samples: pd.DataFrame, library: pd.DataFrame, table_name: str
) -> bool:
    """
    Checks if intersection of samples and libraries table is not null

    Args:
        samples(pd.dataFrame): selected samples table
        libraries (pd.dataFrame): library table
        table_name (str): Name of the table
    """

    if samples.shape[0] == 0 or library.shape[0] == 0:
        return True
    stacked_samples = (
        samples["archive_accession"]
        .str.split(",", expand=True)
        .stack()
        .reset_index(level=0)
        .set_index("level_0")
        .rename(columns={0: "archive_accession"})
        .join(samples.drop("archive_accession", axis=1))
    )

    if table_name in [
        "ancientmetagenome-environmental",
    ]:
        sel_col = ["archive_accession"]
    else:
        sel_col = ["archive_accession", "sample_host"]
    library_selected = library.merge(
        stacked_samples[sel_col],
        left_on="archive_sample_accession",
        right_on="archive_accession",
    )

    if samples.shape[0] != 0 and library_selected.shape[0] == 0:
        return True
    return False
