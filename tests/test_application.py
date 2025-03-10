import os
from amdirt.validate import AMDirValidator


def test_project_multiple_doi(test_data_dir):
    valid_dataset = os.path.join(test_data_dir, "valid.tsv")
    invalid_doi = os.path.join(test_data_dir, "invalid_project_multiple_DOI.tsv")
    schema = os.path.join(test_data_dir, "schema.json")

    valid = AMDirValidator(schema=schema, dataset=valid_dataset)
    invalid = AMDirValidator(schema=schema, dataset=invalid_doi)

    assert valid.check_duplicate_dois() is True

    assert invalid.check_duplicate_dois() is False


def test_multi_values(test_data_dir):
    valid_dataset = os.path.join(test_data_dir, "valid.tsv")
    invalid_multiple_values = os.path.join(
        test_data_dir, "invalid_multi_archive_accession.tsv"
    )
    schema = os.path.join(test_data_dir, "schema.json")

    valid = AMDirValidator(schema=schema, dataset=valid_dataset)
    invalid = AMDirValidator(schema=schema, dataset=invalid_multiple_values)

    assert valid.check_multi_values() is True
    assert invalid.check_multi_values() is False


def test_check_sample_accession(test_data_dir):
    valid_dataset = os.path.join(test_data_dir, "valid_newline.tsv")
    invalid_dataset = os.path.join(
        test_data_dir, "invalid_sample_accession_newline.tsv"
    )
    remote_dataset = os.path.join(test_data_dir, "valid.tsv")
    schema = os.path.join(test_data_dir, "schema.json")

    valid = AMDirValidator(schema=schema, dataset=valid_dataset)
    invalid = AMDirValidator(schema=schema, dataset=invalid_dataset)

    assert valid.check_sample_accession(remote=remote_dataset) is True
    assert invalid.check_sample_accession(remote=remote_dataset) is False
