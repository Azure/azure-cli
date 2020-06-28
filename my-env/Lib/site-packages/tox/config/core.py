from pathlib import Path

from tox.config.sets import ConfigSet
from tox.config.source.api import EnvList
from tox.plugin.impl import impl


@impl
def tox_add_core_config(core: ConfigSet):
    core.add_config(
        keys=["work_dir", "toxworkdir"],
        of_type=Path,
        default=lambda conf, _: conf.core["tox_root"] / ".tox",
        desc="working directory",
    )
    core.add_config(
        keys=["temp_dir"],
        of_type=Path,
        default=lambda conf, _: conf.core["tox_root"] / ".temp",
        desc="temporary directory cleaned at start",
    )
    core.add_config(
        keys=["env_list", "envlist"], of_type=EnvList, default=[], desc="define environments to automatically run",
    )
    core.add_config(
        keys=["skip_missing_interpreters"], of_type=bool, default=True, desc="skip missing interpreters",
    )
