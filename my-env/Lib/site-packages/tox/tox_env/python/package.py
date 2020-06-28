import sys
from abc import ABC, abstractmethod
from typing import List

from packaging.requirements import Requirement

from ..package import PackageToxEnv
from .api import Python


class PythonPackage(Python, PackageToxEnv, ABC):
    def setup(self) -> None:
        """setup the tox environment"""
        super().setup()
        fresh_requires = self.cached_install(self.requires(), PythonPackage.__name__, "requires")
        if not fresh_requires:
            build_requirements = []
            with self._cache.compare(build_requirements, PythonPackage.__name__, "build-requires") as (eq, old):
                if eq is False and old is None:
                    build_requirements.extend(self.build_requires())
                    new_deps = [Requirement(i) for i in set(build_requirements)]
                    self.install_python_packages(packages=new_deps)

    @abstractmethod
    def requires(self) -> List[Requirement]:
        raise NotImplementedError

    @abstractmethod
    def build_requires(self) -> List[Requirement]:
        raise NotImplementedError

    def default_base_python(self, conf, env_name):
        return [sys.executable]
