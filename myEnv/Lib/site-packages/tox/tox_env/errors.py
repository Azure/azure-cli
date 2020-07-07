class Recreate(Exception):
    """Recreate the tox environment"""


class Skip(Exception):
    """Skip this tox environment"""


class Fail(Exception):
    """Failed creating env"""
