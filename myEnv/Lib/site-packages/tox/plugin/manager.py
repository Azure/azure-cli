from typing import List, Type

import pluggy

from tox import provision
from tox.config import core as core_config
from tox.config.cli.parser import ToxParser
from tox.config.sets import ConfigSet
from tox.session.cmd import list_env, show_config, version_flag
from tox.session.cmd.run import parallel, sequential
from tox.tox_env import builder
from tox.tox_env.api import ToxEnv
from tox.tox_env.python.virtual_env import runner
from tox.tox_env.python.virtual_env.package import dev
from tox.tox_env.python.virtual_env.package.artifact import sdist, wheel
from tox.tox_env.register import REGISTER, ToxEnvRegister

from . import spec
from .util import NAME


class Plugin:
    def __init__(self) -> None:
        self.manager = pluggy.PluginManager(NAME)  # type:pluggy.PluginManager
        self.manager.add_hookspecs(spec)

        internal_plugins = (
            provision,
            core_config,
            runner,
            sdist,
            wheel,
            dev,
            parallel,
            sequential,
            list_env,
            version_flag,
            show_config,
        )

        for plugin in internal_plugins:
            self.manager.register(plugin)
        self.manager.load_setuptools_entrypoints(NAME)
        self.manager.register(builder)

        REGISTER.populate(self)
        self.manager.check_pending()

    def tox_add_option(self, parser: ToxParser) -> None:
        self.manager.hook.tox_add_option(parser=parser)

    def tox_add_core_config(self, core: ConfigSet) -> None:
        self.manager.hook.tox_add_core_config(core=core)

    def tox_register_tox_env(self, register: "ToxEnvRegister") -> List[Type[ToxEnv]]:
        return self.manager.hook.tox_register_tox_env(register=register)


MANAGER = Plugin()
