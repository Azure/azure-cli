import sys
from pathlib import Path
from typing import Optional, Sequence

from tox.config.cli.parse import get_options
from tox.config.main import Config
from tox.config.source.ini import Ini
from tox.session.state import State
from tox.tox_env.builder import build_tox_envs


def run(args: Optional[Sequence[str]] = None) -> None:
    try:
        state = setup_state(args)
        command = state.options.command
        handler = state.handlers[command]
        result = handler(state)
        if result is None:
            result = 0
        raise SystemExit(result)
    except KeyboardInterrupt:
        raise SystemExit(-2)


def make_config(path: Path) -> Config:
    tox_ini = path / "tox.ini"
    ini_loader = Ini(tox_ini)
    return Config(ini_loader)


def setup_state(args: Optional[Sequence[str]]) -> State:
    if args is None:
        args = sys.argv[1:]
    options = get_options(*args)
    config = make_config(Path().absolute())
    state = build_tox_envs(config, options, args)
    return state
