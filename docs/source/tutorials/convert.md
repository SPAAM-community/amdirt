# convert

On this page we provide a brief tutorial on how you can use the amdirt command-line-interface (CLI) of the `convert` command.

This tutorial assumes you are on a UNIX based operating system and has internet access. It also assumes you have already installed `amdirt`.

We will show how given a pre-filtered samples or libraries table (e.g. via command line tools or in an R session), in much the same way as the graphical-based `GUI` command, you can use the command-line interface to convert the table to various formats such as download scripts or prepared input sample sheets for ancient metagenomic pipelines.

In this case we will want to download all metagenomic sequencing data of ancient dental calculus samples from Germany, and prepare a sample sheet for the nf-core/eager pipeline.

## Data

We will take use one of the previous releases of AncientMetagenomeDir as an example dataset. You can download the dataset from the following link.

```bash
mkdir amdirt-convert-tutorial
cd amdirt-convert-tutorial
amdirt download --table ancientmetagenome-hostassociated --table_type samples -r v23.09.0
```

## Filter a sample metadata table

Next we can filter the ancient metagenome 'host-associated' sample sheet for all dental calculus tables from Germany.

```bash
cat ancientmetagenome-hostassociated_samples_v23.09.0.tsv | grep -e '^project_name' -e 'dental calculus' | grep -e '^project_name' -e 'Germany' > germany_dentalcalculus.tsv
```

> ⚠ _The command above is not robust and is only used for system portability and demonstration purposes. For example the `Germany` string could be in a site name. In practice, you should use more robust filtering methods such more specific `grep` expressions or in R_.

Now we can use the `convert` command to provide a download script, a nf-core/eager samplesheet, the AncientMetagenomeDir library metadata, and a citations file.

```bash
amdirt convert --curl --eager --librarymetadata --bibliography germany_dentalcalculus.tsv ancientmetagenome-hostassociated
```

This will create the following files:

- `AncientMetagenomeDir_bibliography.bib`: A BiBTeX file with the citations of the samples in the filtered table supplied to `convert`
- `AncientMetagenomeDir_curl_download_script.sh`: A curl download script to download all associated FASTQ files of the samples in the filtered table
- `AncientMetagenomeDir_filtered_libraries.tsv`: A AncientMetagenomeDir _library_ metadata table of the samples in the filtered table
- `AncientMetagenomeDir_nf_core_eager_input_table.tsv`: A nf-core/eager input table for the samples and FASTQ files downloaded from the `curl` script in the filtered table

You could then supply run the `curl` script to download the FASTQ files, and then run the nf-core/eager pipeline with the input table.

```bash
bash AncientMetagenomeDir_curl_download_script.sh
nextflow run nf-core/eager -profile docker --input AncientMetagenomeDir_nf_core_eager_input_table.tsv <...>
```

## Filter a library metadata table

The `convert` command is not just for sample metadata! You can also use it to filter AncientMetagenomeDir library metadata tables.

Let's say of the samples we just downloaded, you realised you only wanted to use the libraries that were with sequenced with a paired-end sequencing kit. We can filter the previously downloaded library metadata table in the same manner as above.

```bash
 grep -e '^project_name' -e 'PAIRED' AncientMetagenomeDir_filtered_libraries.tsv > germany_dentalcalculus_libraries_pe.tsv
```

> ⚠ _The command above is not robust and is only used for system portability and demonstration purposes. For example the `Germany` string could be in a site name. In practice, you should use more robust filtering methods such more specific `grep` expressions or in R_.

We can then again use the `convert` command to provide an updated download script, nf-core/eager samplesheet, and an citations file.

```bash
amdirt convert --curl --eager --bibliography --libraries germany_dentalcalculus_libraries_pe.tsv germany_dentalcalculus.tsv ancientmetagenome-hostassociated
```

> ℹ _It's important to note that you still need a (full or filtered) AncientMetagenomeDir samples sheet even when supplying `--libraries`_.

Once again you will have similar output as above (minus the libraries metadata table), you can than download in this case just the FASTQ files and run these through nf-core eager:

- `AncientMetagenomeDir_bibliography.bib`: A BiBTeX file with the citations of the samples in the filtered table supplied to `convert`
- `AncientMetagenomeDir_curl_download_script.sh`: A curl download script to download all associated FASTQ files of the samples in the filtered table
- `AncientMetagenomeDir_nf_core_eager_input_table.tsv`: A nf-core/eager input table for the samples and FASTQ files downloaded from the `curl` script in the filtered table

You could then supply run the `curl` script to download the FASTQ files, and then run the nf-core/eager pipeline with the input table.

```bash
bash AncientMetagenomeDir_curl_download_script.sh
nextflow run nf-core/eager -profile docker --input AncientMetagenomeDir_nf_core_eager_input_table.tsv <...>
```

## Clean up

Once you've completed this tutorial, simply leave the `amdirt-convert-tutorial` directory and remove it.

For example:

```bash
cd ..
rm -r amdirt-convert-tutorial/
```
