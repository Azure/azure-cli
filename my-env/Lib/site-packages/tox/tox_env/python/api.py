import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, List, Union, cast

from packaging.requirements import Requirement
from virtualenv.discovery.builtin import get_interpreter
from virtualenv.discovery.py_spec import PythonSpec

from tox.config.sets import ConfigSet
from tox.execute.api import Execute
from tox.tox_env.api import ToxEnv
from tox.tox_env.errors import Fail, Recreate


class Python(ToxEnv, ABC):
    def __init__(self, conf: ConfigSet, core: ConfigSet, options, executor: Execute):
        super().__init__(conf, core, options, executor)
        self._python = None
        self._python_search_done = False

    @property
    def py_info(self):
        if self._python is None:
            self._find_base_python()
        return self._python

    def register_config(self):
        super().register_config()
        self.conf.add_config(
            keys=["base_python", "basepython"],
            of_type=List[str],
            default=self.default_base_python,
            desc="environment identifier for python, first one found wins",
        )
        self.conf.add_constant(
            keys=["env_site_packages_dir", "envsitepackagesdir"],
            desc="the python environments site package",
            value=lambda: self.env_site_package_dir(),
        )

    def default_base_python(self, conf, env_name):
        spec = PythonSpec.from_string_spec(env_name)
        if spec.implementation is not None:
            if spec.implementation.lower() in ("cpython", "pypy"):
                return [env_name]
        return [sys.executable]

    def env_site_package_dir(self):
        """
        If we have the python we just need to look at the last path under prefix.
        Debian derivatives change the site-packages to dist-packages, so we need to fix it for site-packages.
        """
        return self.py_info.purelib

    def setup(self) -> None:
        """setup a virtual python environment"""
        super().setup()
        conf = self.python_cache()
        with self._cache.compare(conf, Python.__name__) as (eq, old):
            if eq is False:
                self.create_python_env()
            self._paths = self.paths()

    def _find_base_python(self):
        base_pythons = self.conf["base_python"]
        if self._python_search_done is False:
            self._python_search_done = True
            for base_python in base_pythons:
                python = self.get_python(base_python)
                if python is not None:
                    from virtualenv.run import session_via_cli

                    env_dir = cast(Path, self.conf["env_dir"])
                    session = session_via_cli(
                        [str(env_dir), "--activators", "", "--without-pip", "-p", python.executable],
                    )
                    self._python = session.creator
                    break
        if self._python is None:
            raise NoInterpreter(base_pythons)
        return self._python

    # noinspection PyMethodMayBeStatic
    def get_python(self, base):
        return get_interpreter(base)

    def cached_install(self, deps, section, of_type):
        conf_deps = [str(i) for i in deps]
        with self._cache.compare(conf_deps, section, of_type) as (eq, old):
            if eq is True:
                return True
            if old is None:
                old = []
            missing = [Requirement(i) for i in (set(old) - set(conf_deps))]
            if missing:  # no way yet to know what to uninstall here (transitive dependencies?)
                # bail out and force recreate
                raise Recreate()
            new_deps_str = set(conf_deps) - set(old)
            new_deps = [Requirement(i) for i in new_deps_str]
            self.install_python_packages(packages=new_deps)
        return False

    @abstractmethod
    def python_cache(self) -> Any:
        raise NotImplementedError

    @abstractmethod
    def create_python_env(self) -> List[Path]:
        raise NotImplementedError

    @abstractmethod
    def paths(self) -> List[Path]:
        raise NotImplementedError

    @abstractmethod
    def install_python_packages(self, packages: List[Union[Path, Requirement]], no_deps: bool = False) -> None:
        raise NotImplementedError


class NoInterpreter(Fail):
    """could not find interpreter"""

    def __init__(self, base_pythons):
        self.python = base_pythons
