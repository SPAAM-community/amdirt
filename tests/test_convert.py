from pathlib import Path
import shutil
import os

from amdirt.convert import run_convert


def test_convert_only_sample_df(test_data_dir):
    assert (
        run_convert(
            samples=os.path.join(test_data_dir, "samples_test_convert.tsv"),
            libraries=None,
            table_name="ancientmetagenome-hostassociated",
            eager=True,
            fetchngs=True,
            ameta=True,
            output="test_files",
        )
        is None
    )
    shutil.rmtree("test_files")


def test_convert_only_libraries_df(test_data_dir):
    assert (
        run_convert(
            samples=os.path.join(test_data_dir, "samples_test_convert.tsv"),
            libraries=os.path.join(test_data_dir, "libraries_test_convert.tsv"),
            table_name="ancientmetagenome-hostassociated",
            eager=True,
            fetchngs=True,
            ameta=True,
            output="test_files",
        )
        is None
    )
    shutil.rmtree("test_files")
