from .api import PackageType
from .artifact.sdist import Pep517VirtualEnvPackageSdist
from .artifact.wheel import Pep517VirtualEnvPackageWheel
from .dev import Pep517VirtualEnvPackageDev


def virtual_env_package_id(of_type) -> str:
    if of_type is PackageType.sdist:
        return Pep517VirtualEnvPackageSdist.id()
    elif of_type is PackageType.wheel:
        return Pep517VirtualEnvPackageWheel.id()
    elif of_type is PackageType.dev:
        return Pep517VirtualEnvPackageDev.id()
    raise KeyError(PackageType.name)
