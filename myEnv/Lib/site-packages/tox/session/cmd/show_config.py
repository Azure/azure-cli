from typing import Any, List, Union

from tox.config.cli.parser import ToxParser
from tox.config.sets import ConfigSet
from tox.config.source.api import Command, EnvList
from tox.config.source.ini import IniLoader
from tox.plugin.impl import impl
from tox.session.common import env_list_flag
from tox.session.state import State


@impl
def tox_add_option(parser: ToxParser) -> None:
    our = parser.add_command("config", ["c"], "show tox configuration", display_config)
    our.add_argument("-d", action="store_true", help="list just default envs", dest="list_default_only")
    env_list_flag(our)


def display_config(state: State) -> None:
    first = True
    if not state.options.env:
        print("[tox]")
        print_conf(state.conf.core)
        first = False
    for name in state.env_list:
        tox_env = state.tox_envs[name]
        if not first:
            print()
        first = False
        print(f"[testenv:{name}]")
        print("type = {}".format(type(tox_env).__name__))
        print_conf(tox_env.conf)


def print_conf(conf: ConfigSet) -> None:
    for key in conf:
        value = conf[key]
        result = str_conf_value(value)
        if isinstance(result, list):
            result = "{}{}".format("\n", "\n".join(f"  {i}" for i in result))
        print("{} ={}{}".format(key, " " if result != "" and not result.startswith("\n") else "", result))
    unused = conf.unused()
    if unused:
        print("!!! unused: {}".format(",".join(unused)))


def str_conf_value(value: Any) -> Union[List[str], str]:
    if isinstance(value, dict):
        if not value:
            return ""
        return [f"{k}={v}" for k, v in value.items()]
    elif isinstance(value, (list, set)):
        if not value:
            return ""
        result = []
        for entry in value:
            if isinstance(entry, Command):
                as_str = entry.shell
            elif isinstance(entry, IniLoader):
                as_str = entry.section_name
            else:
                as_str = str(entry)
            result.append(as_str)
        return result
    elif isinstance(value, EnvList):
        return value.envs
    return str(value)
