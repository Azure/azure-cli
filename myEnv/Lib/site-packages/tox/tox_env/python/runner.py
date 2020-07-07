from abc import ABC
from typing import List, Set

from packaging.requirements import Requirement

from tox.tox_env.errors import Skip

from ..runner import RunToxEnv
from .api import NoInterpreter, Python


class PythonRun(Python, RunToxEnv, ABC):
    def register_config(self):
        super().register_config()
        self.conf.add_config(
            keys="deps",
            of_type=List[Requirement],
            default=[],
            desc="Name of the python dependencies as specified by PEP-440",
        )
        self.core.add_config(
            keys=["skip_missing_interpreters"], default=True, of_type=bool, desc="skip running missing interpreters",
        )
        self.add_package_conf()

    def add_package_conf(self):
        if self.core["no_package"] is False:
            self.conf.add_config(
                keys=["extras"], of_type=Set[str], default=[], desc="extras to install of the target package",
            )

    def _find_base_python(self):
        try:
            return super()._find_base_python()
        except NoInterpreter:
            if self.core["skip_missing_interpreters"]:
                raise Skip
            raise

    def setup(self) -> None:
        """setup the tox environment"""
        super().setup()
        self.cached_install(self.conf["deps"], PythonRun.__name__, "deps")

        if self.package_env is not None:
            package_deps = self.package_env.get_package_dependencies(self.conf["extras"])
            self.cached_install(package_deps, PythonRun.__name__, "package_deps")
            self.install_package()

    def install_package(self):
        package = self.package_env.perform_packaging()
        self.install_python_packages(package)
