import json
import pandas as pd
import amdirt.configuration.configuration as config
from amdirt.validate import exceptions
from amdirt.core import logger
from io import StringIO
from pathlib import Path
from rich.table import Table
from rich.console import Console
from dataclasses import dataclass
from jsonschema import Draft7Validator, exceptions as json_exceptions
from typing import AnyStr, BinaryIO, TextIO, Union
import requests
import re
import os

Schema = Union[AnyStr, BinaryIO, TextIO]
Dataset = Union[AnyStr, BinaryIO, TextIO]


@dataclass
class DFError:
    """Class to store DataFrame validation errors"""

    error: str
    source: str
    column: str
    row: str
    message: str
    line_offset: int = (
        2  # Offset to add to row number to account for header and 0 based indexing
    )

    def to_dict(self):
        try:
            column = str(self.column)
            row = str(int(self.row) + self.line_offset)
        except (ValueError, TypeError):
            column = "-"
            row="-"
        return {
            "Error": str(self.error),
            "Source": str(self.source),
            "Column": column,
            "Row": row,
            "Message": str(self.message),
        }

    def to_list(self):
        try:
            column = str(self.column)
            row = str(int(self.row) + self.line_offset)
        except (ValueError, TypeError):
            column = "-"
            row="-"
        return [
        str(i)
        for i in [self.error, self.source, column, row , self.message]
        ]

class DatasetValidator:
    """Dataset as DataFrame validation class"""

    def __init__(self, schema: Schema, dataset: Dataset):
        """Dataset validation class

        Attributes:
            errors (list): List of DFError objects
            dataset_name (str): Dataset name
            schema_name (str): Schema name
            schema (dict): JSON schema
            dataset (pd.DataFrame): Dataset as pandas dataframe
            dataset_json (dict): Dataset as dictionary

        Args:
            schema (Schema): Path to schema in json format
            dataset (Dataset): Path to dataset in tsv format

        """
        self.errors = list()
        self.dataset_path = Path(dataset)
        if str(schema).startswith("http"):
            self.schema_path = schema
        else:
            self.schema_path = Path(schema)
        self.dataset_name = Path(dataset).name
        self.schema_name = Path(schema).name
        self.schema = self.read_schema(schema)
        if self.schema:
            self.dataset = self.read_dataset(dataset, self.schema)
        else:
            self.dataset = False
        self.parsing_ok = (
            True if isinstance(self.dataset, pd.DataFrame) and self.schema else False
        )
        if self.parsing_ok:
            self.dataset_json = self.dataset_to_json()

    def __repr__(self):
        return (
            f"DatasetValidator(schema={self.schema_name}, dataset={self.dataset_name})"
        )

    def add_error(self, err: DFError):
        self.errors.append(err)

    def read_schema(self, schema: Schema) -> dict:
        """Read JSON schema from file or string

        Args:
            schema (str): Path to schema in json format
        Returns:
            dict: JSON schema
        """
        try:
            if str(schema).startswith("http"):
                res = requests.get(schema)
                json_schema = {}
                if res.status_code == 200:
                    json_schema = res.json()
                else:
                    raise Exception("Could not fetch schema from URL")
            else:
                with open(schema, "r") as s:
                    json_schema = json.load(s)
            
            if config.settings.local_json_schema:
                remote_ref_path = "https://spaam-community.github.io/AncientMetagenomeDir/assets/enums/"
                local_ref_path = "file://" + os.path.abspath(config.settings.local_json_schema) + "/"
                
                for key in json_schema["items"]["properties"]:
                    if "$ref" in json_schema["items"]["properties"][key]:
                        val = json_schema["items"]["properties"][key]["$ref"] 
                        val = val.replace(remote_ref_path, local_ref_path)
                        json_schema["items"]["properties"][key]["$ref"] = val
                        
            return json_schema
        except json.JSONDecodeError as e:
            msg = str(e.with_traceback(e.__traceback__))
            self.add_error(
                DFError(
                    error="Schema Error",
                    source=e.msg,
                    column=str(*re.findall(".*column.(\d+).*", msg)),
                    row=int(re.findall(".*line.(\d+).*", msg)[0]),
                    message="JSON parsing error",
                )
            )
            return False

    def read_dataset(self, dataset: Dataset, schema: dict) -> pd.DataFrame:
        """ "Read dataset from file or string
        Args:
            dataset (str): Path to dataset in tsv format
            schema (dict): Parsed schema as dictionary (from read_schema)
        Returns:
            pd.DataFrame: Dataset as pandas dataframe
        """
        string_to_dtype_conversions = {
            "string": str,
            "integer": pd.Int64Dtype(),
            "number": float,
        }
        column_dtypes = {}
        for column_keys in schema["items"]["properties"]:
            coltype = schema["items"]["properties"][column_keys]["type"]
            if isinstance(coltype, list):
                if ("null" in coltype and len(coltype) > 2) or (
                    len(coltype) > 1 and "null" not in coltype
                ):
                    self.add_error(
                        DFError(
                            error="Schema Error",
                            source=coltype,
                            column=column_keys,
                            row="",
                            message="No mixed data types allowed",
                        )
                    )
                    return False
                else:
                    coltype = coltype[0]
            if coltype in string_to_dtype_conversions:
                column_dtypes[column_keys] = string_to_dtype_conversions[coltype]
            elif coltype == "null":
                self.add_error(
                    DFError(
                        error="Schema Error",
                        source=coltype,
                        column=column_keys,
                        row="",
                        message="Default/first type of column in schema can not be null",
                    )
                )
                return False
            else:
                column_dtypes[column_keys] = coltype
        try:
            return pd.read_table(dataset, sep="\t", dtype=column_dtypes)
        except (AttributeError, pd.errors.ParserError, ValueError, TypeError) as e:
            self.add_error(
                DFError(
                    "Dataset Parsing Error",
                    self.dataset_name,
                    '-',
                    '-',
                    e,
                )
            )
            return False

    def check_columns(self) -> bool:
        """Checks if dataset has all required columns

        Returns:
            bool: True if dataset has all required columns, False otherwise
        """
        col_diff = set(self.dataset.columns).difference(
            set(self.schema["items"]["required"])
        )
        try:
            if len(col_diff) != 0:
                raise exceptions.ColumnDifferenceError(
                    f"Dataset has different columns compared to schema {col_diff}"
                )
            else:
                return True
        except exceptions.ColumnDifferenceError as e:
            for c in col_diff:
                self.add_error(DFError(e.name, c, None, None, e.message))
            return False

    def dataset_to_json(self) -> dict:
        """Convert dataset from Pandas DataFrame to JSON

        Returns:
            dict: Dataset as dictionary
        """
        return json.load((StringIO(self.dataset.to_json(orient="records"))))

    def validate_schema(self) -> bool:
        """Validate dataset against JSON schema

        Returns:
            bool: True if dataset is valid, False otherwise
        """
        validator = Draft7Validator(self.schema)
        err_cnt = 0
        for err in validator.iter_errors(self.dataset_json):
            self.add_error(self.cleanup_errors(err))
            err_cnt += 1
        if err_cnt > 0:
            return False
        else:
            return True

    def cleanup_errors(self, error: json_exceptions.ValidationError) -> DFError:
        """Cleans up JSON schema validation errors

        Args:
            error (json_exceptions.ValidationError): JSON schema validation error
        Returns:
            DFError: Cleaned DataFrame error
        """
        err_column = list(error.path)[-1]
        if "enum" in error.schema:
            if len(error.schema["enum"]) > 3:
                error.message = f"'{error.instance}' is not an accepted value.\nPlease check {self.schema['items']['properties'][err_column]['$ref']}"
        err_line = str(error.path[0])
        return DFError(
            "Schema Validation Error",
            error.instance,
            err_column,
            err_line,
            error.message,
        )

    def check_duplicate_rows(self) -> bool:
        """Checks for duplicated rows in dataset

        Returns:
            bool: True if dataset has no duplicated rows, False otherwise
        """
        try:
            dup_df = self.dataset[self.dataset.duplicated(keep=False)]
            if len(dup_df) > 0:
                dup_rows = (
                    dup_df.groupby(dup_df.columns.tolist(), dropna=False)
                    .apply(lambda x: tuple(x.index))
                    .tolist()
                )
                raise exceptions.DuplicateError(f"Rows \n{dup_rows} are duplicated")
        except exceptions.DuplicateError as e:
            for r in dup_rows:
                self.add_error(DFError(e.name, r, None, r, f"Rows {r} are duplicated"))
            return False
        return True

    def to_rich(self):
        """Generate rich output table for console display

        Returns:
            bool: True if dataset is valid
        Raises:
            SystemExit: If dataset is invalid
        """

        table = Table(
            title=f"amdirt Validation Report of {self.dataset_name} against {self.schema_name}"
        )
        columns = ["Error", "Source", "Column", "Row", "Message"]
        for column in columns:
            table.add_column(column, style="red", overflow="fold")
        for error in self.errors:
            table.add_row(*(error.to_list()))

        console = Console()
        if len(self.errors) > 0:
            console.print(table)
            raise SystemExit(f"Invalid dataset {self.dataset_name}")
        else:
            logger.info(f"{self.dataset_name} is valid")
            return True

    def to_markdown(self) -> bool:
        """Generate markdown output table for github display

        Returns:
            bool: True if dataset is valid
        Raises:
            SystemExit: If dataset is invalid
        """
        if len(self.errors) > 0:
            df = pd.concat([pd.Series(error.to_dict()).to_frame().transpose() for error in self.errors])
            raise SystemExit(
                f"Invalid dataset `{self.dataset_name}`\n\n{df.to_markdown(index=False)}"
            )
        else:
            print(f"`{self.dataset_name}` is valid")
            return True
