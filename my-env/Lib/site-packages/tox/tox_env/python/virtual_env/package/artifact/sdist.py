from typing import Any, Dict

from tox.plugin.impl import impl
from tox.tox_env.register import ToxEnvRegister

from .api import Pep517VirtualEnvPackageArtifact


class Pep517VirtualEnvPackageSdist(Pep517VirtualEnvPackageArtifact):
    @property
    def build_type(self) -> str:
        return "sdist"

    @staticmethod
    def id() -> str:
        return "virtualenv-pep-517-sdist"

    @property
    def extra(self) -> Dict[str, Any]:
        return {"config_settings": None}


@impl
def tox_register_tox_env(register: ToxEnvRegister) -> None:
    register.add_package_env(Pep517VirtualEnvPackageSdist)
