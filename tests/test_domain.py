import pytest
import os
from amdirt.validate.domain import DatasetValidator, DFError
from jsonschema import validate
from jsonschema.exceptions import ValidationError as JSONValidationError


def test_DFError():
    err = DFError("test", "test", "test", 0, "test")
    assert err.to_dict() == {
        "Error": "test",
        "Source": "test",
        "Column": "test",
        "Row": "2",
        "Message": "test",
    }
    assert err.to_list() == ["test", "test", "test", "2", "test"]


@pytest.fixture
def schema():
    schema = {
        "type": "object",
        "properties": {
            "sample": {"type": "string"},
            "weight": {"type": "number"},
        },
    }
    return schema


@pytest.fixture
def valid_dataset():
    instance = {"sample": "bone", "weight": 10}
    return instance


@pytest.fixture
def invalid_dataset():
    instance = {"sample": 10, "weight": "bone"}
    return instance


def test_jsonschema_validator(valid_dataset, invalid_dataset, schema):

    assert validate(instance=valid_dataset, schema=schema) is None
    with pytest.raises(JSONValidationError):
        assert validate(instance=invalid_dataset, schema=schema)

def test_schema_parsing(test_data_dir):
    valid_dataset = os.path.join(test_data_dir, "valid.tsv")
    schema = os.path.join(test_data_dir, "schema.json")
    invalid_schema_too_many_types = os.path.join(test_data_dir, "invalid_schema_too_many_types.json")
    invalid_schema_parsing = os.path.join(test_data_dir, "invalid_schema_parsing.json")

    assert DatasetValidator(schema=schema, dataset=valid_dataset)

    assert DatasetValidator(schema=invalid_schema_too_many_types, dataset=valid_dataset).parsing_ok is False

    assert DatasetValidator(schema=invalid_schema_parsing, dataset=valid_dataset).parsing_ok is False


def test_dataset_parsing(test_data_dir):
    valid_dataset = os.path.join(test_data_dir, "valid.tsv")
    invalid_dataset_too_many_columns = os.path.join(
        test_data_dir, "invalid_too_many_columns.tsv"
    )
    invalid_dataset_invalid_dtype_in_col = os.path.join(
        test_data_dir, "invalid_dtype_in_col.tsv"
    )
    schema = os.path.join(test_data_dir, "schema.json")

    assert DatasetValidator(schema=schema, dataset=valid_dataset)

    assert DatasetValidator(schema, invalid_dataset_too_many_columns).parsing_ok is False

    assert DatasetValidator(schema, invalid_dataset_invalid_dtype_in_col).parsing_ok is False


def test_column_name(test_data_dir):
    valid_dataset = os.path.join(test_data_dir, "valid.tsv")
    invalid_column_name = os.path.join(test_data_dir, "invalid_column_name.tsv")
    schema = os.path.join(test_data_dir, "schema.json")

    valid = DatasetValidator(schema=schema, dataset=valid_dataset)
    invalid = DatasetValidator(schema=schema, dataset=invalid_column_name)

    assert valid.check_columns() is True

    assert invalid.check_columns() is False


def test_duplicate_row(test_data_dir):
    valid_dataset = os.path.join(test_data_dir, "valid.tsv")
    invalid_dataset = os.path.join(test_data_dir, "invalid_duplicate_row.tsv")
    schema = os.path.join(test_data_dir, "schema.json")

    validator_valid = DatasetValidator(schema=schema, dataset=valid_dataset)
    validator_invalid = DatasetValidator(schema, invalid_dataset)

    assert validator_valid.check_duplicate_rows() is True
    assert validator_invalid.check_duplicate_rows() is False


def test_schema_validation(test_data_dir):
    valid_dataset = os.path.join(test_data_dir, "valid.tsv")
    invalid_dataset = os.path.join(test_data_dir, "invalid_schema.tsv")
    schema = os.path.join(test_data_dir, "schema.json")

    validator_valid = DatasetValidator(schema=schema, dataset=valid_dataset)

    assert validator_valid.validate_schema() is True

    assert validator_valid.check_columns() is True

    validator_invalid = DatasetValidator(schema, invalid_dataset)

    assert validator_invalid.validate_schema() is False

    with pytest.raises(SystemExit):
        validator_invalid.to_rich()

    with pytest.raises(SystemExit):
        validator_invalid.to_markdown()
