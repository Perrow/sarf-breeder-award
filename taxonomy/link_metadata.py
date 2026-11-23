import ipaddress
import socket
import ssl
from contextlib import contextmanager
from http.client import HTTPSConnection
from urllib.parse import quote, urlsplit

from django.core.validators import URLValidator


validate_https_url = URLValidator(schemes=["https"])


def parse_https_url(url):
    validate_https_url(url)
    parts = urlsplit(url)
    if parts.username is not None or parts.password is not None or parts.port not in (None, 443):
        raise ValueError("Artlänkar måste använda HTTPS på port 443 utan användaruppgifter.")
    return parts


def _is_public_address(address):
    ip = ipaddress.ip_address(address)
    if not ip.is_global or ip.is_multicast:
        return False
    if isinstance(ip, ipaddress.IPv6Address):
        # Exclude mapped, translation and transition addresses.
        return ip in ipaddress.IPv6Network("2000::/3") and not (ip.sixtofour or ip.teredo)
    return True


@contextmanager
def open_public_https(parts):
    host = parts.hostname.encode("idna").decode("ascii")
    addresses = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    if not addresses or any(not _is_public_address(address[4][0]) for address in addresses):
        raise ValueError("Artlänken måste gå till en publik adress.")

    context = ssl.create_default_context()
    connection = HTTPSConnection(host, timeout=5, context=context)
    target = quote(parts.path or "/", safe="/%:@!$&'()*+,;=-._~")
    if parts.query:
        target += "?" + quote(parts.query, safe="/%?:@!$&'()*+,;=-._~")

    # Connect to a validated socket address without resolving the hostname
    # again. The original hostname still controls certificate verification.
    try:
        for family, socktype, protocol, _, address in addresses:
            try:
                with socket.socket(family, socktype, protocol) as sock:
                    sock.settimeout(5)
                    sock.connect(address)
                    connection.sock = context.wrap_socket(sock, server_hostname=host)
                break
            except OSError as error:
                last_error = error
        else:
            raise last_error

        connection.request(
            "GET", target, headers={"User-Agent": "BreederAwardsSpeciesImporter/1.0"}
        )
        with connection.getresponse() as response:
            yield response
    finally:
        connection.close()
