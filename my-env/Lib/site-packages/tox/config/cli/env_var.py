import logging
import os

from tox.config.source.ini import StrConvert

CONVERT = StrConvert()


def get_env_var(key, of_type):
    """Get the environment variable option.

    :param key: the config key requested
    :param of_type: the type we would like to convert it to
    :return:
    """
    key_upper = key.upper()
    for fmt in ("TOX_{}", "TOX{}"):
        environ_key = fmt.format(key_upper)
        if environ_key in os.environ:
            value = os.environ[environ_key]
            # noinspection PyBroadException
            try:
                source = f"env var {environ_key}"
                of_type = CONVERT.to(raw=value, of_type=of_type)
                return of_type, source
            except Exception as exception:
                logging.warning(
                    "env var %s=%r cannot be transformed to %r because %r", environ_key, value, of_type, exception,
                )


__all__ = ("get_env_var",)
