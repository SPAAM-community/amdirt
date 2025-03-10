from amdirt.download import download


def test_download():
    table = "ancientmetagenome-hostassociated"
    table_type = "samples"
    release = "v23.12.0"

    d = download(table, table_type, release, output=".")
    assert d == "ancientmetagenome-hostassociated_samples_v23.12.0.tsv"
