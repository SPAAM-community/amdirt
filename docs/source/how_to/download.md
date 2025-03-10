# download

## What

Download a copy of an AncientMetagenomeDir table.

## When

This command would be used when you want to download an AncientMetagenomeDir table locally.

You typically do this if you're planning to use the `convert` command later.

## How

```bash
amdirt download --table ancientsinglegenome-hostassociated --table_type samples -r v23.12.0 -o .
```

## Output

This example command above will download the `ancientsinglegenome-hostassociated` `sample` table from the `v23.12.0` AncientMetagenomeDir release, and save it locally to `ancientmetagenome-hostassociated_samples_v23.12.0.tsv`
