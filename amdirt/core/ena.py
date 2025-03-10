import requests
from amdirt.core import logger
import os
from typing import List, Dict


class ENA:
    """Class for querying the ENA API"""

    def __init__(self) -> None:
        self.base_url = "https://www.ebi.ac.uk/ena"

    def __repr__(self) -> str:
        """Display URL of API documentation"""
        return f"The documentation for the {self.__class__.__name__} API can be found at {self.base_url}"

    def status(self) -> bool:
        """Check if API is up

        Returns:
            bool: True if API is up, False otherwise
        """
        try:
            resp = requests.get(self.base_url)
            if resp.status_code == 200:
                return True
            else:
                return False
        except requests.exceptions.ConnectionError:
            return False

    def doc(self, dir: str = ".") -> None:
        """Get PDF documentation for API

        Args:
            dir(str): path to output PDF directory
        """
        r = requests.get(self.base_url + "doc")
        pdf = os.path.join(
            os.path.expanduser(dir), f"{self.__class__.__name__}_APIDocumentation.pdf"
        )
        with open(pdf, "wb") as fw:
            fw.write(r.content)
        logger.info(
            f"{self.__class__.__name__} documentation has been written to {pdf}"
        )

    def __get_json__(self, url: str) -> List[Dict]:
        """Get json content from URL

        Args:
            url(str): URL to get json content from
        Returns:
            List[Dict]: json content
        """
        resp = requests.get(url)
        if resp.status_code == 200:
            if len(resp.json()) > 0:
                return resp.json()
            else:
                logger.warning("No results found")
                return []


class ENABrowserAPI(ENA):
    """Class to interact with the ENA Browser API"""

    def __init__(self) -> None:
        super().__init__()
        self.base_url = "https://www.ebi.ac.uk/ena/browser/api/"


class ENAPortalAPI(ENA):
    """Class to interact with the ENA Portal API"""

    def __init__(self) -> None:
        """ENA Portal API class

        Attributes:
            base_url(str): base URL for ENA Portal API
        """
        super().__init__()
        self.base_url = "https://www.ebi.ac.uk/ena/portal/api/"

    def _get_results(self) -> List[Dict]:
        """Get list of available results

        Returns:
            List[Dict]: list of available results
        """
        url = os.path.join(self.base_url, "results?dataPortal=ena&format=json")
        json_resp = self.__get_json__(url)
        return json_resp

    def list_results(self) -> None:
        """Display list of available results

        Returns:
            List[Dict]: list of available results
        """
        json_resp = self._get_results()
        for result in json_resp:
            logger.info(f"{result['resultId']} - {result['description']}")
        return json_resp

    def _get_fields(self, result_type: str) -> List:
        """Get list of available fields

        Args:
            result_type(str): A result is a set of data that can
            be searched against and returned
        Returns:
            List: list of available fields
        """
        url = os.path.join(
            self.base_url,
            f"returnFields?dataPortal=ena&format=json&result={result_type}",
        )
        json_resp = self.__get_json__(url)
        return json_resp

    def list_fields(self, result_type: str) -> None:
        """Display list of available fields

        Args:
            result_type(str): A result is a set of data that can
            be searched against and returned
        Returns:
            List: list of available fields
        """
        json_resp = self._get_fields(result_type=result_type)
        for field in json_resp:
            logger.info(f"{field['columnId']} - {field['description']}")
        logger.info(f"Available fields for {result_type} are: {json_resp}")

    def _check_result_type(self, result_type: str) -> bool:
        """Check if result type is allowed

        Args:
            result_type(str): A result is a set of data that can
            be searched against and returned
        Returns:
            bool: True if result type is valid, False otherwise
        """
        all_results = self._get_results()
        results = [result["resultId"] for result in all_results]
        if result_type not in results:
            logger.warning(f"{result_type} is not a valid result type")
            return False
        return True

    def _check_fields(self, result_type: str, fields: List[str]) -> bool:
        """Check if fields are allowed

        Args:
            result_type(str): A result is a set of data that can
            be searched against and returned
            fields(List): list of fields to check
        Returns:
            bool: True if fields are valid, False otherwise
        """
        all_fields = self._get_fields(result_type)
        fields = [field["columnId"] for field in all_fields]
        for field in fields:
            if field not in fields:
                logger.warning(f"{field} is not a valid field")
                return False
        return True

    def query(
        self,
        accession: str,
        result_type: str = "read_run",
        fields: List = [
            "run_accession",
            "sample_accession",
            "fastq_ftp",
            "fastq_md5",
            "fastq_bytes",
        ],
    ) -> dict:
        """Generate list of runs metadata for a study accession

        Args:
            accession (str): ENA accession
            result_type(str): A result is a set of data that can
            be searched against and returned
            fields(List): list of fields to return

        Returns:
            dict: run_accession as keys, and metadata as values
        """

        self._check_result_type(result_type)
        self._check_fields(result_type, fields)
        url = os.path.join(
            self.base_url,
            f"filereport?accession={accession}&download=false&format=json&result={result_type}&fields={','.join(fields)}",
        )
        json_resp = self.__get_json__(url)
        return json_resp


if __name__ == "__main__":
    e = ENAPortalAPI()
    print(e.query("PRJEB30331"))
