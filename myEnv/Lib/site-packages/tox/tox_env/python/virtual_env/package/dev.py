from pathlib import Path
from typing import List

from tox.plugin.impl import impl
from tox.tox_env.register import ToxEnvRegister

from .api import Pep517VirtualEnvPackage


class Pep517VirtualEnvPackageDev(Pep517VirtualEnvPackage):
    def perform_packaging(self) -> List[Path]:
        """no build operation defined for this yet, just an install flag of the package directory"""
        return [self.core["tox_root"]]

    @staticmethod
    def id() -> str:
        return "virtualenv-pep-517-dev"


@impl
def tox_register_tox_env(register: ToxEnvRegister) -> None:
    register.add_package_env(Pep517VirtualEnvPackageDev)
