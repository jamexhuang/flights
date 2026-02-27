import os
from abc import ABC

from ..querying import Query, ReturnQuery

try:
    import dotenv  # pip install python-dotenv

    dotenv.load_dotenv()

except ModuleNotFoundError:
    pass


class Integration(ABC):
    """Represents an integration."""

    def fetch_html(self, q: Query | ReturnQuery | str, /) -> str:
        """Fetch the flights page HTML from a query.

        Args:
            q: The query.  Can be a :class:`Query`, :class:`ReturnQuery`,
                or a plain string.
        """
        raise NotImplementedError


def get_env(k: str, /) -> str:
    """(utility) Get environment variable.

    If nothing found, raises an error.

    Returns:
        str: The value.
    """
    try:
        return os.environ[k]
    except KeyError:
        raise OSError(f"could not find environment variable: {k!r}")
