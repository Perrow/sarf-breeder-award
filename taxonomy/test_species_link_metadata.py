from email.message import Message
from io import BytesIO
from unittest.mock import patch

from django.test import SimpleTestCase

from .species_import import _fetch_page_title, _source_name_from_url


class _HtmlResponse(BytesIO):
    def __init__(self, content):
        super().__init__(content)
        self.headers = Message()
        self.headers["Content-Type"] = "text/html; charset=utf-8"

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


class SpeciesLinkMetadataTests(SimpleTestCase):
    @patch("taxonomy.species_import.urlopen")
    def test_fetch_page_title_reads_and_normalizes_html_title(self, urlopen):
        urlopen.return_value = _HtmlResponse(
            b"<html><head><title>  FishBase &amp; species   page </title></head></html>"
        )

        title = _fetch_page_title("https://www.fishbase.se/example")

        self.assertEqual(title, "FishBase & species page")

    def test_known_sources_get_readable_names(self):
        self.assertEqual(_source_name_from_url("https://www.fishbase.se/example"), "FishBase")
        self.assertEqual(_source_name_from_url("https://planetcatfish.com/example"), "PlanetCatfish")
        self.assertEqual(_source_name_from_url("https://www.ciklid.org/artregister/"), "NCS Artregister")
