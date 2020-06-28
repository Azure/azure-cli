"""Hook specifications for tox - see https://pluggy.readthedocs.io/"""
from argparse import ArgumentParser
from typing import Type

import pluggy

from tox.config.sets import ConfigSet
from tox.tox_env.api import ToxEnv
from tox.tox_env.register import ToxEnvRegister

from .util import NAME

hook_spec = pluggy.HookspecMarker(NAME)


# noinspection PyUnusedLocal
@hook_spec
def tox_add_option(parser: ArgumentParser) -> None:
    """add cli flags"""


# noinspection PyUnusedLocal
@hook_spec
def tox_add_core_config(core: ConfigSet) -> None:
    """add options to the core section of the tox"""


# noinspection PyUnusedLocal
@hook_spec
def tox_register_tox_env(register: ToxEnvRegister) -> Type[ToxEnv]:
    """register new tox environment types that can have their own argument"""
