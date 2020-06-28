from abc import ABC
from pathlib import Path
from typing import List, Optional

from tox.config.sets import ConfigSet
from tox.config.source.api import Command, EnvList
from tox.execute.api import Execute

from .api import ToxEnv
from .package import PackageToxEnv


class RunToxEnv(ToxEnv, ABC):
    def __init__(self, conf: ConfigSet, core: ConfigSet, options, execute: Execute):
        super().__init__(conf, core, options, execute)
        self.package_env = None  # type: Optional[PackageToxEnv]

    def register_config(self):
        super().register_config()
        self.conf.add_config(
            keys=["description"], of_type=str, default=None, desc="description attached to the tox environment",
        )
        self.conf.add_config(
            keys=["commands"], of_type=List[Command], default=[], desc="the commands to be called for testing",
        )
        self.conf.add_config(
            keys=["commands_pre"], of_type=List[Command], default=[], desc="the commands to be called before testing",
        )
        self.conf.add_config(
            keys=["commands_post"], of_type=List[Command], default=[], desc="the commands to be called after testing",
        )
        self.conf.add_config(
            keys=["change_dir", "changedir"],
            of_type=Path,
            default=lambda conf, name: conf.core["tox_root"],
            desc="Change to this working directory when executing the test command.",
        )
        self.conf.add_config(
            "depends",
            of_type=EnvList,
            desc="tox environments that this environment depends on (must be run after those)",
            default=[],
        )
        self.conf.add_config(
            "parallel_show_output",
            of_type=bool,
            default=False,
            desc="if set to True the content of the output will always be shown  when running in parallel mode",
        )

    def set_package_env(self):
        if self.core["no_package"]:
            return
        res = self.package_env_name_type()
        if res is not None:
            package_tox_env = yield res
            self.package_env = package_tox_env

    def package_env_name_type(self):
        raise NotImplementedError

    def has_package(self):
        return self.package_env_name_type() is not None

    def clean(self, package_env=True):
        super().clean()
        if self.package_env:
            self.package_env.clean()
