from amdirt.core import (
    get_colour_chemistry,
    doi2bib,
    ena,
)


def test_get_colour_chemistry():

    assert get_colour_chemistry("Illumina HiSeq 2500") == 4
    assert get_colour_chemistry("Illumina NovaSeq 6000") == 2


def test_doi2bib():
    assert doi2bib("10.1038/nature14236")[:18] == " @article{Mnih_201"


def test_ena_portal_status():
    ena_portal = ena.ENAPortalAPI()
    assert ena_portal.status() is True


def test_ena_browser_status():
    ena_browser = ena.ENABrowserAPI()
    assert ena_browser.status() is True
