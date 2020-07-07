from configparser import ConfigParser, NoSectionError

from tox.plugin.impl import impl
from tox.tox_env.python.virtual_env.package.artifact.wheel import Pep517VirtualEnvPackageWheel
from tox.tox_env.register import ToxEnvRegister

from ..runner import PythonRun
from .api import VirtualEnv
from .package.api import PackageType
from .package.util import virtual_env_package_id


class VirtualEnvRunner(VirtualEnv, PythonRun):
    """local file system python virtual environment via the virtualenv package"""

    @staticmethod
    def id() -> str:
        return "virtualenv"

    def add_package_conf(self):
        if self.core["no_package"] is True:
            return
        self.conf.add_config(
            keys="package",
            of_type=str,
            default=PackageType.sdist.name,
            desc="package installation mode - {} ".format(" | ".join(i.name for i in PackageType)),
            post_process=lambda key, conf: PackageType[key],
        )
        if self.conf["package"] == PackageType.skip:
            return
        super().add_package_conf()
        self.core.add_config(
            keys=["package_env", "isolated_build_env"],
            of_type=str,
            default=".package",
            desc="tox environment used to package",
        )
        package = self.conf["package"]
        self.conf.add_config(
            keys="package_tox_env_type",
            of_type=str,
            default=virtual_env_package_id(package),
            desc="tox package type used to package",
        )
        if self.conf["package"] is PackageType.wheel:
            self.conf.add_config(
                keys="universal_wheel",
                of_type=bool,
                default=Pep517VirtualEnvPackageWheel.default_universal_wheel(self.core),
                desc="tox package type used to package",
            )

    def default_universal_wheel(self):
        parser = ConfigParser()
        success = parser.read(filenames=[str(self.core["tox_root"] / "setup.cfg")])
        universal = False
        if success:
            try:
                universal = parser.get("bdist_wheel", "universal") == "1"
            except NoSectionError:
                pass
        return universal

    def has_package(self):
        return self.core["no_package"] or self.conf["package"] is not PackageType.skip

    def package_env_name_type(self):
        if self.has_package():
            package = self.conf["package"]
            package_env_type = self.conf["package_tox_env_type"]
            name = self.core["package_env"]
            # we can get away with a single common package if: sdist, dev, universal wheel
            if package is PackageType.wheel and self.conf["universal_wheel"] is False:
                # if version specific wheel one per env
                name = "{}-{}".format(name, self.conf["env_name"])
            return name, package_env_type

    def install_package(self):
        package = self.package_env.perform_packaging()
        develop = self.conf["package"] is PackageType.dev
        self.install_python_packages(package, no_deps=True, develop=develop, force_reinstall=True)


@impl
def tox_register_tox_env(register: ToxEnvRegister):
    register.add_run_env(VirtualEnvRunner)
