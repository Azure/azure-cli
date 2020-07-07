import sys
from typing import List

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name
from packaging.version import Version

from tox.config.sets import ConfigSet
from tox.plugin.impl import impl
from tox.session.state import State
from tox.tox_env.api import ToxEnv
from tox.version import __version__ as current_version

if sys.version_info >= (3, 8):
    from importlib.metadata import distribution
else:
    from importlib_metadata import distribution


def add_tox_requires_min_version(requires, conf):
    min_version = conf.core["min_version"]
    requires.append(Requirement(f"tox >= {min_version}"))
    return requires


def provision(state: State):
    core = state.conf.core
    provision_tox_env = core["provision_tox_env"]
    requires = core["requires"]

    exists = set()
    missing = []
    for package in requires:
        package_name = canonicalize_name(package.name)
        if package_name not in exists:
            exists.add(package_name)
            dist = distribution(package.name)
            if not package.specifier.contains(dist.version, prereleases=True):
                missing.append(package)
    if missing:
        for package in missing:
            print(package)
        run_provision(requires, state.tox_envs[provision_tox_env])


@impl
def tox_add_core_config(core: ConfigSet):
    core.add_config(
        keys=["min_version", "minversion"],
        of_type=Version,
        default=current_version,
        desc="Define the minimal tox version required to run",
    )
    core.add_config(
        keys="provision_tox_env",
        of_type=str,
        default=".tox",
        desc="Name of the virtual environment used to provision a tox.",
    )
    core.add_config(
        keys="requires",
        of_type=List[Requirement],
        default=[],
        desc="Name of the virtual environment used to provision a tox.",
        post_process=add_tox_requires_min_version,
    )
    core.add_config(
        keys=["no_package", "app", "skip_sdist"],
        of_type=bool,
        default=False,
        desc="Is there any packaging involved in this project.",
    )


# noinspection PyUnusedLocal
def run_provision(deps: List[Requirement], tox_env: ToxEnv):
    """"""
