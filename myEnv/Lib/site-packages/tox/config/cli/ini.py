import logging
import os
from pathlib import Path
from typing import cast

from appdirs import user_config_dir

from tox.config.source.ini import Ini, IniLoader

DEFAULT_CONFIG_FILE = Path(user_config_dir("tox")) / "config.ini"


class IniConfig:
    TOX_CONFIG_FILE_ENV_VAR = "TOX_CONFIG_FILE"
    STATE = {None: "failed to parse", True: "active", False: "missing"}

    section = "tox"

    def __init__(self):
        config_file = os.environ.get(self.TOX_CONFIG_FILE_ENV_VAR, None)
        self.is_env_var = config_file is not None
        self.config_file = Path(config_file if config_file is not None else DEFAULT_CONFIG_FILE)
        self._cache = {}

        self.has_config_file = self.config_file.exists()
        if self.has_config_file:
            self.config_file = self.config_file.absolute()
            try:
                self.ini = Ini(self.config_file)
                # noinspection PyProtectedMember
                self.has_tox_section = cast(IniLoader, self.ini.core)._section is not None
            except Exception as exception:
                logging.error("failed to read config file %s because %r", config_file, exception)
                self.has_config_file = None

    def get(self, key, of_type):
        # noinspection PyBroadException
        cache_key = key, of_type
        if cache_key in self._cache:
            result = self._cache[cache_key]
        else:
            try:
                source = "file"
                value = self.ini.core.load(key, of_type=of_type, conf=None)
                result = value, source
            except KeyError:  # just not found
                result = None
            except Exception as exception:
                logging.warning(
                    "%s key %s as type %r failed with %r", self.config_file, key, of_type, exception,
                )
                result = None
        self._cache[cache_key] = result
        return result

    def __bool__(self):
        return bool(self.has_config_file) and bool(self.has_tox_section)

    @property
    def epilog(self):
        msg = "{}config file {!r} {} (change{} via env var {})"
        return msg.format(
            os.linesep,
            str(self.config_file),
            self.STATE[self.has_config_file],
            "d" if self.is_env_var else "",
            self.TOX_CONFIG_FILE_ENV_VAR,
        )
