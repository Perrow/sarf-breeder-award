import unicodedata

from django.db.backends.signals import connection_created


CASE_INSENSITIVE_COLLATION = "uca1400_swedish_as_ci"
CASE_SENSITIVE_COLLATION = "utf8mb4_bin"


def _compare(left, right):
    return (left > right) - (left < right)


def _case_insensitive_compare(left, right):
    left_key = unicodedata.normalize("NFC", left).casefold()
    right_key = unicodedata.normalize("NFC", right).casefold()
    return _compare(left_key, right_key)


def _register_on_sqlite(sender, connection, **kwargs):
    if connection.vendor != "sqlite":
        return
    connection.connection.create_collation(
        CASE_INSENSITIVE_COLLATION,
        _case_insensitive_compare,
    )
    connection.connection.create_collation(CASE_SENSITIVE_COLLATION, _compare)


def register_sqlite_collations():
    connection_created.connect(
        _register_on_sqlite,
        dispatch_uid="breeder_awards.register_sqlite_collations",
    )
