from typing import Dict

from tox.config.cli.parser import ToxParser
from tox.execute.api import Outcome
from tox.plugin.impl import impl
from tox.session.common import env_list_flag
from tox.session.state import State
from tox.tox_env.api import ToxEnv

from .common import env_run_create_flags
from .single import run_one


@impl
def tox_add_option(parser: ToxParser) -> None:
    our = parser.add_command("run", ["r"], "run environments", run_sequential)
    env_list_flag(our)
    env_run_create_flags(our)


def run_sequential(state: State) -> int:
    status_codes = {}  # type:Dict[str, int]
    for name in state.env_list:
        tox_env = state.tox_envs[name]
        status_codes[name] = run_one(tox_env, state.options.recreate, state.options.no_test)
    return report(status_codes, state.tox_envs)


# noinspection PyUnusedLocal
def report(status_dict: Dict[str, int], tox_envs: Dict[str, ToxEnv]) -> int:
    for name, status in status_dict.items():
        if status == Outcome.OK:
            msg = "OK  "
        else:
            msg = f"FAIL code {status}"
        print(f"  {name}: {msg}")
    if all(value == Outcome.OK for name, value in status_dict.items()):
        print("  congratulations :)")
        return Outcome.OK
    else:
        print("  evaluation failed :(")
        return -1
