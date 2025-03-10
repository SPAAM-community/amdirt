# validate

## What

The purpose of the `validate` command is to check that an AncientMetagenomeDir metadata file confirms the specifications of the project.

## When

In most cases, `validate` is run for you via automatic Pull Request checks on the AncientMetagenomeDir GitHub repository.

However in some cases, you may wish to run this manually yourself before opening your pull request.

## How

Before you run `validate`, you normally need a local copy of AncientMetagenomeDir, but primarily the AncientMetagenomeDir `.tsv` file, and the corresponding `.json` schema file.

To run, execute the following command:

```bash
amdirt validate ancientmetagenome-hostassociated_samples.tsv ancientmetagenome-hostassociated_samples_schema.json
```

With the `.tsv` file in the first positional argument, and the `.json` schema in the second position.

`validate` can be run on both sample and library tables.

By default, no schema validation checks will be performed however it will check the files can be loaded as expected.

The tool offers different types of validations that are activated by options.

- **schema validation** (`-s`): compares the TSV against the schema
- **duplicate line checking** (`-d`): checks there are no duplicate lines
- **column presence/absence checking** (`-c`): checks that all expected columns are present
- **doi duplication checking** (`-i`): checks there are not the same DOI across two different publications
- **ENA accession validation** (`-a`): checks the ENA accession code is valid and corresponds to the PRJ associated code
- **multi-value column checking**: allows you to check there are no duplicates within a comma separate column with multiple values (e.g. sample accessions)

You can also change the output console formatting from a python-rich format (default) to a markdown formatting with (`-m`). The markdown formatting is primarily for the AncientMetagenomeDir automatic checks on GitHub.

For example, to check all columns are present, there are no duplicate lines, and the table matches the schema you can run

```bash
amdirt validate -s -d ancientmetagenome-hostassociated_samples.tsv ancientmetagenome-hostassociated_samples_schema.json
```

If the table is valid you will get a corresponding message as follows:

```bash
2022-12-16 11:15:41.109 INFO    amdirt: ancientmetagenome-hostassociated_samples.tsv is valid
```

If the table is invalid, you will get a table containing a list of the found errors:

```text
           amdirt Validation Report of ancientmetagenome-hostassociated_samples.tsv against ancientmetagenome-hostassociated_samples_schema.json
┏━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Error                   ┃ Source     ┃ Column      ┃ Row ┃ Message                                                                                       ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Schema Validation Error │ Homo saens │ sample_host │ 3   │ 'Homo saens' is not an accepted value.                                                        │
│                         │            │             │     │ Please check                                                                                  │
│                         │            │             │     │ https://spaam-community.github.io/AncientMetagenomeDir/assets/enums/sample_host.json          │
│ Schema Validation Error │ -1243.386  │ latitude    │ 5   │ -1243.386 is less than the minimum of -90                                                     │
└─────────────────────────┴────────────┴─────────────┴─────┴───────────────────────────────────────────────────────────────────────────────────────────────┘
Invalid dataset ancientmetagenome-hostassociated_samples.tsv
```

Where `Source` is the problematic cell entry, the `Column` and `Row` where the error is found, and the reason why it is problematic in the `Message`.

> ⚠️ _The row index includes the header! For example row 3 correpsonds to the the second_ sample _row in the table._

You can then use this information to correct your table before opening your GitHub pull request to the AncientMetagenomeDir repository.
