from abc import ABC, abstractmethod
from typing import Any, List

from tox.config.sets import ConfigSet
from tox.execute.api import Execute
from tox.tox_env.errors import Recreate

from .api import ToxEnv


class PackageToxEnv(ToxEnv, ABC):
    def __init__(self, conf: ConfigSet, core: ConfigSet, options, executor: Execute):
        super().__init__(conf, core, options, executor)
        self._cleaned = False
        self._setup_done = False

    def register_config(self):
        super().register_config()

    @abstractmethod
    def get_package_dependencies(self, extras=None) -> List[Any]:
        raise NotImplementedError

    @abstractmethod
    def perform_packaging(self) -> List[Any]:
        raise NotImplementedError

    def clean(self):
        # package environments may be shared clean only once
        if self._cleaned is False:
            self._cleaned = True
            super().clean()

    def ensure_setup(self):
        if self._setup_done is False:
            try:
                self.setup()
            except Recreate:
                self.clean()
                self.setup()
