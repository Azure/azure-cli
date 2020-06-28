from configparser import ConfigParser, NoSectionError
from typing import Any, Dict

from tox.plugin.impl import impl
from tox.tox_env.register import ToxEnvRegister

from .api import Pep517VirtualEnvPackageArtifact


class Pep517VirtualEnvPackageWheel(Pep517VirtualEnvPackageArtifact):
    @staticmethod
    def default_universal_wheel(core):
        parser = ConfigParser()
        success = parser.read(filenames=[str(core["tox_root"] / "setup.cfg")])
        universal = False
        if success:
            try:
                universal = parser.get("bdist_wheel", "universal") == "1"
            except NoSectionError:
                pass
        return universal

    @property
    def build_type(self) -> str:
        return "wheel"

    @property
    def extra(self) -> Dict[str, Any]:
        return {
            "config_settings": {"--global-option": ["--bdist-dir", str(self.conf["env_dir"] / "build")]},
            "metadata_directory": str(self.meta_folder) if self.meta_folder.exists() else None,
        }

    @staticmethod
    def id() -> str:
        return "virtualenv-pep-517-wheel"


@impl
def tox_register_tox_env(register: ToxEnvRegister) -> None:
    register.add_package_env(Pep517VirtualEnvPackageWheel)
