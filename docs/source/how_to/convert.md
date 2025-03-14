# convert

## What

The purpose of the `convert` command is to convert AncientMetagenomeDir tables to input sheets for different pipelines and software. It will also download citation information for you.

It is a partial command-line equivalent to the `viewer` graphical user interface.

## When

You typically will use `convert` if you are a command-line power user, and have already performed table filtering and sample selection programmatically (e.g. in R or python), rather than using the amdirt `viewer` graphical-user-interface.

## How

The following description assumes that you have already have an AncientMetagenomeDir **samples** table that has been filtered to the samples you wish to run through a given pipeline(s).

> ⚠️ _The header, and present columns etc. should match exactly that on AncientMetagenomeDir, only rows may be removed._

To generate sample sheets of the support pipelines: open a terminal (activating software environments if necessary, see [amdirt Installation Page](https://github.com/SPAAM-community/amdirt/)), and there you can run the following command (an example being a filtered `ancientmetagenome-hostassociated_samples_warinnersamplesonly.tsv` table):

```bash
mkdir samplesheets/
amdirt convert ancientmetagenome-hostassociated_samples_warinnersamplesonly.tsv ancientmetagenome-hostassociated -o samplesheets/ --<tool>
```

where you provide the filtered TSV, which AncientMetagenomeDir samples table the filtered table is derived from,then the output directory where the samplesheets should be saved into, and which tool to generate a samplesheet from.

Alternatively, if you only want specific libraries, and already have pre-filtered the associated AncientMetagenomeDir libraries table, you can also provide it. Here for example:

- the filtered sample table is : `ancientmetagenome-hostassociated_samples_warinnersamplesonly.tsv`
- the matching filtered libraries table is: `ancientmetagenome-hostassociated_libraries_warinnerlibrariesonly.tsv`

```bash
mkdir -p samplesheets/
amdirt convert --libraries ancientmetagenome-hostassociated_libraries_warinnerlibrariesonly.tsv ancientmetagenome-hostassociated_samples_warinnersamplesonly.tsv ancientmetagenome-hostassociated -o samplesheets/ --<tool>
```

See [Output](#output) for descriptions of all output files.

> ⚠️ _When using a **pipeline input samplesheet**, you should always double check the sheet is correctly configured. We cannot guarantee accuracy between metadata and sequencing files._

Once you have validated it, you can directly supply it to the appropriate pipeline as follows (using nf-core/eager as an example):

```bash
nextflow run nf-core/eager <...> --input ancientMetagenomeDir_eager_input.csv
```

The **citations BibTex** file contains all the citation information of your selected samples in a widely used format called BibTex. You can import this file into most referencing or bibliography managing tools (Zotero, Paperpile etc.).

> ⚠️ _Occasionally the cross-ref databases do not have citation information for certain publications. You will receive a warning if so, with the relevant DOIs for you to manually get this information._

## Output

> ⚠️ _We highly recommend generating and reviewing `AncientMetagenomeDir_filtered_libraries.tsv` **before** downloading or running any pipelines to ensure you have in the download scripts and/or pipeline input sheets only the actual library types you wish to use (e.g. you may only want paired-end data, or non-UDG treated data)._

> ⚠️ _To use a **pipeline input samplesheet**, you should always double check the sheet is correctly configured. We cannot guarantee accuracy between metadata and sequencing files._

All possible output is as follows:

- `<outdir>`: where all the pipeline samplesheets are placed (by default `.`)
- `AncientMetagenomeDir_bibliography.bib`:
  - A BibTex format citation information file with all references (where available) present in the filtered sample table. In case a library table is provided using `--libraries`, only the references relevant to the selected libraries are reported.
- `AncientMetagenomeDir_filtered_libraries.tsv`:
  - The associated AncientMetagenomeDir curated metadata for all _libraries_ of the samples in the input table.
- `AncientMetagenomeDir_curl_download_script.sh`:
  - A bash script containing curl commands for all libraries in the input samples list.
- `AncientMetagenomeDir_aspera_download_script.sh`:
  - A bash script containing Aspera commands for all libraries in the input samples list. See [How Tos](/how_to/miscellaneous) for Aspera configuration information.
- `AncientMetagenomeDir_nf_core_fetchngs_input_table.tsv`:
  - An input sheet containing ERS/SRS accession numbers in a format compatible with the [nf-core/fetchngs](https://nf-co.re/fetchngs) input samplesheet.
- `AncientMetagenomeDir_nf_core_eager_input_table.tsv`:
  - An input sheet with metadata in a format compatible with the [nf-core/eager](https://nf-co.re/eager) input samplesheet.
  - Contained paths are relative to the directory output when using the `curl` and `aspera` download scripts (i.e., input sheet assumes files are in the same directory as the input sheet itself).
- `AncientMetagenomeDir_nf_core_taxprofiler_input_table.csv`:
  - An input sheet with metadata in a format compatible with the [nf-core/taxprofiler](https://nf-co.re/eager) input samplesheet.
  - Contained paths are relative to the directory output when using the `curl` and `aspera` download scripts (i.e., input sheet assumes files are in the same directory as the input sheet itself).
- `AncientMetagenomeDir_aMeta_input_table.tsv`:
  - An input sheet with metadata in a format compatible with the [aMeta](https://github.com/NBISweden/aMeta) input samplesheet.
  - Contained paths are relative to the directory output when using the `curl` and `aspera` download scripts (i.e., input sheet assumes files are in the same directory as the input sheet itself).
- `AncientMetagenomeDir_nf_core_mag_input_{single,paired}_table.csv`:
  - An input sheet with metadata in a format compatible with the [nf-core/mag](https://nf-co.re/eager) input samplesheet.
  - Contained paths are relative to the directory output when using the `curl` and `aspera` download scripts (i.e., input sheet assumes files are in the same directory as the input sheet itself).
  - nf-core/mag does not support paired- and single-end data in the same run, therefore two sheets will be generated if your selected samples contain both types of libraries.
