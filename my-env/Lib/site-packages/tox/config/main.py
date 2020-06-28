from collections import OrderedDict
from pathlib import Path

from .sets import ConfigSet
from .source.api import Source


class Config:
    def __init__(self, config_source: Source) -> None:
        self._src = config_source
        self.core = self._setup_core(self._src)
        self._env_names = list(self._src.envs(self.core))
        self._envs = OrderedDict()

    def _setup_core(self, config_source):
        core = ConfigSet(config_source.core, self)
        core.add_config(
            keys=["tox_root", "toxinidir"],
            of_type=Path,
            default=config_source.tox_root,
            desc="the root directory (where the configuration file is found)",
        )
        from tox.plugin.manager import MANAGER

        MANAGER.tox_add_core_config(core)
        return core

    def __getitem__(self, item):
        try:
            return self._envs[item]
        except KeyError:
            env = ConfigSet(self._src[item], self)
            self._envs[item] = env
            return env

    def __iter__(self):
        return iter(self._env_names)

    def __repr__(self):
        return "{}(config_source={!r})".format(type(self).__name__, self._src)

    def __contains__(self, item):
        return item in self._envs
