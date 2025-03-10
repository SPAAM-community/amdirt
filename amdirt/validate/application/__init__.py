from typing import Iterable, AnyStr, Union
from amdirt.validate.domain import DatasetValidator, DFError
from amdirt.core import get_json_path
from amdirt.core.diff import get_sample_diff
from amdirt.core.ena import ENAPortalAPI
from rich.progress import track
from pathlib import Path
import pandas as pd
import json


class AMDirValidator(DatasetValidator):
    """Validator Class for AncientMetagenomeDir datasets"""

    def check_duplicate_dois(self) -> bool:
        if "publication_doi" in self.dataset:
            doi_col = "publication_doi"
        else:
            doi_col = "data_publication_doi"
        project_dois = self.dataset.groupby("project_name")[
            doi_col
        ].unique()
        doi_unique = self.dataset.groupby("project_name")[
            doi_col
        ].nunique()
        err_cnt = 0
        for project in doi_unique.index:
            if doi_unique[project] > 1:
                err_cnt += 1
                self.add_error(
                    DFError(
                        error="Duplicated DOI Error",
                        source=project_dois[project],
                        column="publication_doi",
                        row="",
                        message=f"Duplicate DOI for {project} project. Make sure each project has a single DOI",
                    )
                )
        if err_cnt > 0:
            return False
        return True

    def check_multi_values(
        self, column_names: Iterable[str] = ["archive_accession"]
    ) -> bool:
        """Check for duplicates entries in multi values column
        Args:
            column_names (Iterable[str], optional): List of multi values columns to check for duplications. Defaults to ["archive_accession"].
        """
        err_cnt = 0
        for column in column_names:
            row = 0
            for archives in self.dataset[column]:
                archives = archives.split(",")
                if len(set(archives)) != len(archives):
                    self.add_error(
                        DFError(
                            error="Duplicates in multi values column",
                            source=archives,
                            column=column,
                            row=row,
                            message=f"Duplicates in multi values column {column}. Make sure each value in combination is unique",
                        )
                    )
                    err_cnt += 1
                row += 1
        if err_cnt > 0:
            return False
        else:
            return True

    def check_sample_accession(self, remote: Union[AnyStr, None] = None) -> bool:
        """Check that sample accession are valid

        Args:
            remote (AnyStr | None, optional): Remote to check against. Defaults to None.
        """
        if not remote:
            with open(get_json_path()) as f:
                tables = json.load(f)
            samples = tables["samples"]
            for table in samples:
                if self.dataset_name == Path(samples[table]).name:
                    remote = samples[table]
            if remote is None:
                raise SystemExit(
                    f"No remote found for {self.dataset} dataset, please provide one"
                )
        remote_samples = DatasetValidator(schema=self.schema_path, dataset=remote)
        df_change = pd.concat([remote_samples.dataset, self.dataset]).drop_duplicates(
            keep=False
        )
        df_change.drop_duplicates(
            inplace=True, keep="last", subset=list(df_change.columns)[:-1]
        )
        is_ok = True
        
        print(df_change)

        if df_change.shape[0] > 0:
            e = ENAPortalAPI()
            change_dict = {}

            for i in df_change.index:
                try:
                    supported_archive = df_change.loc[i, "archive"] in ["SRA", "ENA"]
                except ValueError as e:
                    print(e)
                    print(df_change.loc[i, :])
                    supported_archive = False
                    continue
                if supported_archive:
                    samples = df_change.loc[i, "archive_accession"].split(",")
                    project = df_change.loc[i, "archive_project"]
                    if project not in change_dict:
                        change_dict[project] = {"index": i, "sample": samples}
                    else:
                        change_dict[project]["sample"].extend(samples)
                else:
                    continue

            for project in track(change_dict, description="Checking ENA/SRA accessions..."):
                json_result = e.query(
                    accession=project,
                    result_type="read_experiment",
                    fields=["secondary_sample_accession"],
                )
                ena_samples = []
                for i in json_result:
                    ena_samples.append(i["secondary_sample_accession"])
                for sample in change_dict[project]["sample"]:
                    if sample not in ena_samples:
                        row = df_change.query(
                            f"archive_accession.str.contains('{sample}') and archive_project.str.contains('{project}')"
                        ).index[0]
                        self.add_error(
                            DFError(
                                error="Invalid sample accession",
                                source=sample,
                                column="archive_accession",
                                row=row,
                                message=f"Sample accession {sample} is not a valid ENA/SRA sample accession for the project {project}",
                            )
                        )
                        is_ok = False
        return is_ok
