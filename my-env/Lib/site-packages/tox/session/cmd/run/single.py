from typing import List, cast

from tox.config.source.api import Command
from tox.execute.api import Outcome
from tox.tox_env.api import ToxEnv
from tox.tox_env.errors import Recreate
from tox.tox_env.runner import RunToxEnv


def run_one(tox_env: RunToxEnv, recreate: bool, no_test: bool) -> int:
    if recreate:
        tox_env.clean(package_env=recreate)
    try:
        tox_env.setup()
    except Recreate:
        tox_env.clean(package_env=False)  # restart creation once, no package please
        tox_env.setup()

    code = run_commands(tox_env, no_test)
    return code


def run_commands(tox_env: ToxEnv, no_test: bool) -> int:
    status = Outcome.OK  # assume all good
    if no_test is False:
        keys = ("commands_pre", "commands", "commands_post")
        for key in keys:
            for cmd in cast(List[Command], tox_env.conf[key]):
                current_status = tox_env.execute(
                    cmd.args, cwd=tox_env.conf["change_dir"], allow_stdin=True, show_on_standard=True,
                )
                if current_status.exit_code != Outcome.OK:
                    return status
    return status


__all__ = ("run_one",)
