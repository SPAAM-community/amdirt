# autofill and merge

## What

The purpose of the `autofill` command is to help AncientMetagenomeDir contributors to fill the metadata library tables for new studies, while the `merge` will help integrate these new metadata to the AncientMetagenomeDir master tables.

## When

You should use these commands when you want to contribute to AncientMetagenomeDir, by adding a newly published dataset, if it's already available on a sequencing archive (ENA/SRA).

It is normally executed for you by a 'bot' on GitHub when you have opened a pull-request with a samplesheet, by leaving a comment of `@spaam-bot autofill <ancientmetagenomedir table name> <project id>`. Thus, you should also only run this command if you want to do your AncientMetagenomeDir _entirely_ locally.

## How

### `autofill`

amdirt `autofill` is a command line only tool. To use it, you first need to have amdirt installed, and have access to it through a terminal.

You will need two information:

- The accession number(s) of the dataset, for example `PRJEB56776`
- The type of samples of this new dataset, one of `ancientmetagenome-environmental`, `ancientmetagenome-hostassociated`, `ancientsinglegenome-hostassociated`

It is then just a matter of passing them as arguments to amdirt `autofill`:

```bash
$ amdirt autofill -n ancientmetagenome-hostassociated -l libraries.tsv -s samples.tsv PRJEB56776
amdirt [INFO]: ancientmetagenome-hostassociated_libraries.tsv is valid
amdirt [INFO]: ENA API is up
amdirt [INFO]: Found 15 libraries
amdirt [INFO]: Writing libraries metadata to libraries.tsv
amdirt [INFO]: Found 15 samples
amdirt [INFO]: Writing samples metadata to samples.tsv
amdirt [WARNING]: Sample name must match that reported in publication and/or sample-level table. ENA reported sample-name may not be correct! Check before submission.
```

amdirt `autofill` has created two files, one with the library metadata information (`libraries.tsv`) and one with the sample metadata information (`samples.tsv`).

```bash
$ head -n 10 libraries.tsv| cut -c1-80
project_name publication_year data_publication_doi sample_name archive archive_project
   LZP5.2T  PRJEB56776 ERS13577724 LZP5.2T  NextSeq 550 SINGLE WGS 21055508 ERR1043
   LZP10T  PRJEB56776 ERS13577725 LZP10T  NextSeq 550 SINGLE WGS 18667881 ERR104307
   LZP11.4K  PRJEB56776 ERS13577726 LZP11.4K     NextSeq 550 SINGLE WGS 13224117 ERR10
   LZP13.4K  PRJEB56776 ERS13577727 LZP13.4K     NextSeq 550 SINGLE WGS 23176476 ERR10
   LZP18T  PRJEB56776 ERS13577728 LZP18T  NextSeq 550 SINGLE WGS 20898948 ERR104307
   LZP19.4K  PRJEB56776 ERS13577729 LZP19.4K     NextSeq 550 SINGLE WGS 15766490 ERR10
   LZP20K  PRJEB56776 ERS13577730 LZP20K  NextSeq 550 SINGLE WGS 23770102 ERR104307
   LZP22K  PRJEB56776 ERS13577731 LZP22K  NextSeq 550 SINGLE WGS 18941737 ERR104307
   LZP25K  PRJEB56776 ERS13577732 LZP25K  NextSeq 550 SINGLE WGS 14753980 ERR104307
```

You will notice that some columns are missing information, especially in the sample metadata table (in this example, `samples.tsv`). Despite our best efforts, not all information is made available through ENA, and it will be up to you to fill these missing columns, from the original publication, its supplementary material, or elsewhere.
You can do it in your favorite text editor, or table editor (like LibreOffice Calc, or Excel).
Please refer to the AncientMetagenomeDir wiki for information on this process: [https://github.com/SPAAM-community/AncientMetagenomeDir/wiki](https://github.com/SPAAM-community/AncientMetagenomeDir/wiki).

> ⚠️ The sample and library names reported on sequencing archives (ENA, SRA, ...) might not be the same as the one list in the original article. Please double check before proceeding further.

### `merge`

Once all metadata have been filled in, both for the libraries, and samples tables, you can now attempt to merge it with the AncientMetagenomeDir master table, using the amdirt `merge` command

First, the libraries table:

```bash
$ amdirt merge -n ancientmetagenome-hostassociated -t libraries libraries.tsv
amdirt [INFO]: New Dataset is valid
amdirt [INFO]: Merging new dataset with remote ancientmetagenome-hostassociated libraries dataset
amdirt [INFO]: New ancientmetagenome-hostassociated libraries dataset written to ./ancientmetagenome-hostassociated_libraries.tsv
```

Then the samples table

```bash
$ amdirt merge -n ancientmetagenome-hostassociated -t samples samples.tsv
amdirt [INFO]: New Dataset is valid
amdirt [INFO]: Merging new dataset with remote ancientmetagenome-hostassociated samples dataset
amdirt [INFO]: New ancientmetagenome-hostassociated samples dataset written to ./ancientmetagenome-hostassociated_samples.tsv
```

And... that's it. You've successfully used `autofill` and `merge` ! Don't forget to add and commit, and open a pull request against the AncientMetagenomeDir master branch.
