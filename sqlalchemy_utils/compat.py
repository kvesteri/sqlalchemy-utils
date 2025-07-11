import re
from importlib.metadata import metadata


def get_sqlalchemy_version(version=metadata('sqlalchemy')['Version']):
    """Extract the sqlalchemy version as a tuple of integers."""

    match = re.search(r'^(\d+)(?:\.(\d+)(?:\.(\d+))?)?', version)
    try:
        return tuple(int(v) for v in match.groups() if v is not None)
    except AttributeError:
        return ()
