import click
from amdirt import __version__

from amdirt.validate import run_validation
from amdirt.viewer import run_app
from amdirt.convert import run_convert
from amdirt.core import get_json_path, get_amdir_tags, get_latest_tag
from amdirt.autofill import run_autofill
from amdirt.merge import merge_new_df
from amdirt.download import download as download_amdir
from json import load


class MutuallyExclusiveOption(click.Option):
    # Credits goes to Stan Chang for this code snippet
    # https://gist.github.com/stanchan/bce1c2d030c76fe9223b5ff6ad0f03db

    def __init__(self, *args, **kwargs):
        self.mutually_exclusive = set(kwargs.pop("mutually_exclusive", []))
        help = kwargs.get("help", "")
        if self.mutually_exclusive:
            ex_str = ", ".join(self.mutually_exclusive)
            kwargs["help"] = help + (
                " NOTE: This argument is mutually exclusive with "
                " arguments: [" + ex_str + "]."
            )
        super(MutuallyExclusiveOption, self).__init__(*args, **kwargs)

    def handle_parse_result(self, ctx, opts, args):
        if self.mutually_exclusive.intersection(opts) and self.name in opts:
            raise click.UsageError(
                "Illegal usage: `{}` is mutually exclusive with "
                "arguments `{}`.".format(self.name, ", ".join(self.mutually_exclusive))
            )

        return super(MutuallyExclusiveOption, self).handle_parse_result(ctx, opts, args)


def get_table_list():
    json_path = get_json_path()
    with open(json_path, "r") as f:
        table_list = load(f)
        return list(table_list["samples"].keys())


@click.group()
@click.version_option(__version__)
@click.pass_context
@click.option("--verbose", is_flag=True, help="Verbose mode")
def cli(ctx, verbose, no_args_is_help=True, **kwargs):
    """\b
    amdirt: Performs validity check of AncientMetagenomeDir datasets
    Authors: amdirt development team and the SPAAM community
    Homepage & Documentation: https://github.com/SPAAM-community/amdirt
    \b
    """
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    pass


####################
# Validation  tool #
####################


@cli.command()
@click.argument("dataset", type=click.Path(exists=True))
@click.argument("schema", type=click.Path(exists=True))
@click.option("-s", "--schema_check", is_flag=True, help="Turn on schema checking.")
@click.option(
    "-d", "--line_dup", is_flag=True, help="Turn on line duplicate line checking."
)
@click.option(
    "-c", "--columns", is_flag=True, help="Turn on column presence/absence checking."
)
@click.option("-i", "--doi", is_flag=True, help="Turn on DOI duplicate checking.")
@click.option(
    "--multi_values",
    multiple=True,
    help="Check multi-values column for duplicate values.",
)
@click.option(
    "-a",
    "--online_archive",
    is_flag=True,
    help="Turn on ENA accession validation",
)
@click.option(
    "--remote",
    type=click.Path(),
    default=None,
    help="[Optional] Path/URL to remote reference sample table for archive accession validation",
)
@click.option(
    "-l",
    "--local_json_schema",
    type=click.Path(writable=True),
    help="path to folder with local JSON schemas",
)
@click.option("-m", "--markdown", is_flag=True, help="Output is in markdown format")
@click.pass_context
def validate(ctx, no_args_is_help=True, **kwargs):
    """\b
    Run validity check of AncientMetagenomeDir datasets
    \b
    DATASET: path to tsv file of dataset to check
    SCHEMA: path to JSON schema file
    """
    run_validation(**kwargs, **ctx.obj)


###############################
# Interactive viewing/filtering  tool #
###############################


@cli.command()
@click.option(
    "-t",
    "--tables",
    type=click.Path(exists=True),
    help="JSON file listing AncientMetagenomeDir tables",
)
@click.pass_context
def viewer(ctx, no_args_is_help=True, **kwargs):
    """Launch interactive filtering tool"""
    run_app(**kwargs, **ctx.obj)


###################
# Conversion tool #
###################


@cli.command()
@click.argument("samples", type=click.Path(exists=True))
@click.argument("table_name", type=str)
@click.option(
    "-t",
    "--tables",
    type=click.Path(exists=True),
    help="(Optional) JSON file listing AncientMetagenomeDir tables",
)
@click.option(
    "--libraries",
    type=click.Path(readable=True, file_okay=True, dir_okay=False, exists=True),
    help=("(Optional) Path to a pre-filtered libraries table"),
    cls=MutuallyExclusiveOption,
    mutually_exclusive=["librarymetadata"],
)
@click.option(
    "--librarymetadata",
    is_flag=True,
    help="Generate AncientMetagenomeDir libraries table of all samples in input table",
    cls=MutuallyExclusiveOption,
    mutually_exclusive=["libraries"],
)
@click.option(
    "-o",
    "--output",
    type=click.Path(writable=True, dir_okay=True, file_okay=False),
    default=".",
    show_default=True,
    help="conversion output directory",
)
@click.option(
    "--bibliography",
    is_flag=True,
    help="Generate BibTeX file of all publications in input table",
)
@click.option(
    "--dates",
    is_flag=True,
    help="Generate AncientMetagenomeDir dates table of all samples in input table"
)
@click.option(
    "--curl",
    is_flag=True,
    help="Generate bash script with curl-based download commands for all libraries of samples in input table",
)
@click.option(
    "--aspera",
    is_flag=True,
    help="Generate bash script with Aspera-based download commands for all libraries of samples in input table",
)
@click.option(
    "--fetchngs",
    is_flag=True,
    help="Convert filtered samples and libraries tables to nf-core/fetchngs input tables",
)
@click.option(
    "--sratoolkit",
    is_flag=True,
    help="Generate bash script with SRA Toolkit fasterq-dump based download commands for all libraries of samples in input table",
)
@click.option(
    "--eager",
    is_flag=True,
    help="Convert filtered samples and libraries tables to eager input tables",
)
@click.option(
    "--ameta",
    is_flag=True,
    help="Convert filtered samples and libraries tables to aMeta input tables",
)
@click.option(
    "--mag",
    is_flag=True,
    help="Convert filtered samples and libraries tables to nf-core/mag input tables",
)
@click.option(
    "--taxprofiler",
    is_flag=True,
    help="Convert filtered samples and libraries tables to nf-core/taxprofiler input tables",
)
@click.pass_context
def convert(ctx, no_args_is_help=True, **kwargs):
    """\b
    Converts filtered samples and libraries tables to eager, ameta, taxprofiler, and fetchNGS input tables

    Note: When supplying a pre-filtered libraries table with `--libraries`, the corresponding sample table is still required!

    \b
    SAMPLES: path to filtered AncientMetagenomeDir samples tsv file
    TABLE_NAME: name of table to convert
    """
    run_convert(**kwargs, **ctx.obj)


#################
# Autofill tool #
#################


@cli.command()
@click.argument("accession", type=str, nargs=-1)
@click.option(
    "-n",
    "--table_name",
    type=click.Choice(get_table_list()),
    default="ancientmetagenome-hostassociated",
    show_default=True,
)
@click.option(
    "-t",
    "--output_ena_table",
    type=click.Path(writable=True),
    help="path to ENA table output file",
)
@click.option(
    "-l",
    "--library_output",
    type=click.Path(writable=True),
    help="path to library output table file",
)
@click.option(
    "-s",
    "--sample_output",
    type=click.Path(writable=True),
    help="path to sample output table file",
)
@click.pass_context
def autofill(ctx, no_args_is_help=True, **kwargs):
    """\b
    Autofills library and/or sample table(s) using ENA API and accession numbers
    \b

    ACCESSION: ENA accession(s). Multiple accessions can be space separated (e.g. PRJNA123 PRJNA456)
    """
    run_autofill(**kwargs, **ctx.obj)


################
# Merging tool #
################


@cli.command()
@click.argument("dataset", type=click.Path(exists=True))
@click.option(
    "-n",
    "--table_name",
    type=click.Choice(get_table_list()),
    default="ancientmetagenome-hostassociated",
    show_default=True,
)
@click.option(
    "-t",
    "--table_type",
    type=click.Choice(["samples", "libraries"]),
    default="libraries",
    show_default=True,
)
@click.option("-m", "--markdown", is_flag=True, help="Output is in markdown format")
@click.option(
    "-o",
    "--outdir",
    type=click.Path(writable=True),
    default=".",
    show_default=True,
    help="path to sample output table file",
)
@click.pass_context
def merge(ctx, no_args_is_help=True, **kwargs):
    """\b
    Merges new dataset with existing table
    \b

    DATASET: path to tsv file of new dataset to merge
    """
    merge_new_df(**kwargs, **ctx.obj)


@cli.command()
@click.option(
    "-t",
    "--table",
    help="AncientMetagenomeDir table to download",
    type=click.Choice(get_table_list()),
    default="ancientmetagenome-hostassociated",
    show_default=True,
)
@click.option(
    "-y",
    "--table_type",
    help="Type of table to download",
    type=click.Choice(["samples", "libraries", "dates"]),
    default="samples",
    show_default=True,
)
@click.option(
    "-r",
    "--release",
    help="Release tag to download",
    type=click.Choice(get_amdir_tags()),
    default=get_latest_tag(get_amdir_tags()),
    show_default=True,
)
@click.option(
    "-o",
    "--output",
    help="Output directory",
    type=click.Path(writable=True),
    default=".",
    show_default=True,
)
def download(no_args_is_help=True, **kwargs):
    """\b
    Download a table from the amdirt repository
    """
    download_amdir(**kwargs)


if __name__ == "__main__":
    cli()
