from email.message import Message
from io import BytesIO
from unittest.mock import patch

from django.test import SimpleTestCase

from .species_import import (
    SpeciesImportError,
    _fetch_page_title,
    _link_list,
    _source_name_from_url,
)


class _HtmlResponse(BytesIO):
    def __init__(self, content):
        super().__init__(content)
        self.status = 200
        self.headers = Message()
        self.headers["Content-Type"] = "text/html; charset=utf-8"

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


class SpeciesLinkMetadataTests(SimpleTestCase):
    @patch("taxonomy.species_import.open_public_https")
    def test_fetch_page_title_reads_and_normalizes_html_title(self, open_public_https):
        open_public_https.return_value = _HtmlResponse(
            b"<html><head><title>  FishBase &amp; species   page </title></head></html>"
        )

        title = _fetch_page_title("https://www.fishbase.se/example")

        self.assertEqual(title, "FishBase & species page")

    def test_link_import_rejects_unsafe_or_invalid_urls(self):
        for url in (
            "http://www.fishbase.se/example",
            "file:///etc/example",
            "https://user@www.fishbase.se/",
            "https://www.fishbase.se:8080/",
            "inte en url",
        ):
            with self.subTest(url=url), self.assertRaises(SpeciesImportError):
                _link_list({"links": [{"url": url}]})

    @patch("taxonomy.link_metadata.socket.socket")
    @patch("taxonomy.link_metadata.socket.getaddrinfo")
    def test_title_lookup_never_connects_to_nonpublic_addresses(self, resolve, socket):
        for address in ("127.0.0.1", "10.0.0.3", "::1", "::ffff:127.0.0.1"):
            with self.subTest(address=address):
                resolve.return_value = [(0, 0, 0, "", (address, 443))]
                self.assertEqual(_fetch_page_title("https://www.fishbase.se/"), "")
        socket.assert_not_called()

    @patch("taxonomy.link_metadata.socket.socket")
    @patch("taxonomy.link_metadata.socket.getaddrinfo")
    @patch("taxonomy.link_metadata.ssl.create_default_context")
    def test_redirect_targets_are_validated(self, ssl, resolve, connect):
        response = connect.return_value.__enter__.return_value
        tls = ssl.return_value.wrap_socket.return_value
        tls.makefile.return_value = BytesIO(
            b"HTTP/1.1 302 Found\r\nLocation: https://localhost/\r\nContent-Length: 0\r\n\r\n"
        )
        resolve.side_effect = [
            [(2, 1, 6, "", ("8.8.8.8", 443))],
            [(2, 1, 6, "", ("127.0.0.1", 443))],
        ]

        self.assertEqual(_fetch_page_title("https://www.fishbase.se/"), "")
        response.connect.assert_called_once_with(("8.8.8.8", 443))
        self.assertEqual(resolve.call_count, 2)

    def test_known_sources_get_readable_names(self):
        self.assertEqual(_source_name_from_url("https://www.fishbase.se/example"), "FishBase")
        self.assertEqual(_source_name_from_url("https://planetcatfish.com/example"), "PlanetCatfish")
        self.assertEqual(_source_name_from_url("https://www.ciklid.org/artregister/"), "NCS Artregister")
