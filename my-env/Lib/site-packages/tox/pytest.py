import os
import sys
import textwrap
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence

import pytest

import tox.run
from tox.execute.api import Outcome
from tox.execute.request import shell_cmd
from tox.report import LOGGER
from tox.run import run as tox_run
from tox.run import setup_state as previous_setup_state
from tox.session.cmd.run.parallel import ENV_VAR_KEY
from tox.session.state import State


@pytest.fixture(autouse=True)
def ensure_logging_framework_not_altered():
    before_handlers = list(LOGGER.handlers)
    yield
    LOGGER.handlers = before_handlers


def check_os_environ():
    old = os.environ.copy()
    to_clean = {k: os.environ.pop(k, None) for k in {ENV_VAR_KEY, "TOX_WORK_DIR", "PYTHONPATH"}}

    yield

    for key, value in to_clean.items():
        if value is not None:
            os.environ[key] = value

    new = os.environ
    extra = {k: new[k] for k in set(new) - set(old)}
    extra.pop("PLAT", None)
    miss = {k: old[k] for k in set(old) - set(new)}
    diff = {
        "{} = {} vs {}".format(k, old[k], new[k])
        for k in set(old) & set(new)
        if old[k] != new[k] and not k.startswith("PYTEST_")
    }
    if extra or miss or diff:
        msg = "test changed environ"
        if extra:
            msg += f" extra {extra}"
        if miss:
            msg += f" miss {miss}"
        if diff:
            msg += f" diff {diff}"
        pytest.fail(msg)


check_os_environ_stable = pytest.fixture(autouse=True)(check_os_environ)


@pytest.fixture(name="tox_project")
def init_fixture(tmp_path, capsys, monkeypatch):
    def _init(files: Dict[str, Any]):
        """create tox  projects"""
        return ToxProject(files, tmp_path, capsys, monkeypatch)

    return _init


@pytest.fixture()
def empty_project(tox_project, monkeypatch):
    project = tox_project({"tox.ini": ""})
    monkeypatch.chdir(project.path)
    return project


class ToxProject:
    def __init__(self, files: Dict[str, Any], path: Path, capsys, monkeypatch):
        self.path = path  # type: Path
        self._capsys = capsys
        self.monkeypatch = monkeypatch
        self._setup_files(self.path, files)

    @staticmethod
    def _setup_files(dest: Path, content: Dict[str, Any]) -> None:
        for key, value in content.items():
            if not isinstance(key, str):
                raise TypeError(f"{key!r} at {dest}")  # pragma: no cover
            at_path = dest / key
            if isinstance(value, dict):
                at_path.mkdir(exist_ok=True)
                ToxProject._setup_files(at_path, value)
            elif isinstance(value, str):
                at_path.write_text(textwrap.dedent(value))
            else:
                msg = "could not handle {} with content {!r}".format(at_path / key, value)  # pragma: no cover
                raise TypeError(msg)  # pragma: no cover

    @property
    def structure(self):
        result = {}
        for dir_name, _, files in os.walk(str(self.path)):
            dir_path = Path(dir_name)
            into = result
            relative = dir_path.relative_to(str(self.path))
            for elem in relative.parts:
                into = into.setdefault(elem, {})
            for file_name in files:
                into[file_name] = (dir_path / file_name).read_text()
        return result

    def config(self):
        return tox.run.make_config(self.path)

    def run(self, *args) -> "ToxRunOutcome":
        cur_dir = os.getcwd()
        state = None
        os.chdir(str(self.path))
        try:
            self._capsys.readouterr()  # start with a clean state - drain
            code = None
            state = None

            def our_setup_state(value):
                nonlocal state
                state = previous_setup_state(value)
                return state

            with self.monkeypatch.context() as m:
                m.setattr(tox.run, "setup_state", our_setup_state)
                try:
                    tox_run(args)
                except SystemExit as exception:
                    code = exception.code
            out, err = self._capsys.readouterr()
            return ToxRunOutcome(args, self.path, code, out, err, state)
        finally:
            os.chdir(cur_dir)

    def __repr__(self):
        return "{}(path={}) at {}".format(type(self).__name__, self.path, id(self))


ToxProjectCreator = Callable[[Dict[str, Any]], ToxProject]


class ToxRunOutcome:
    def __init__(self, cmd: Sequence[str], cwd: Path, code: int, out: str, err: str, state: Optional[State]) -> None:
        extended_cmd = [sys.executable, "-m", "tox"]
        extended_cmd.extend(cmd)
        self.cmd = extended_cmd  # type: List[str]
        self.cwd = cwd  # type: Path
        self.code = code  # type:int
        self.out = out  # type:str
        self.err = err  # type: str
        self.state = state  # type:Optional[State]

    @property
    def success(self) -> bool:
        return self.code == Outcome.OK

    def assert_success(self) -> None:
        if not self.success:
            assert repr(self)

    def __repr__(self):
        return "\n".join(
            "{}{}{}".format(k, "\n" if "\n" in v else ": ", v)
            for k, v in (
                ("code", str(self.code)),
                ("cmd", self.shell_cmd),
                ("cwd", str(self.cwd)),
                ("standard output", self.out),
                ("standard error", self.err),
            )
            if v
        )

    @property
    def shell_cmd(self):
        return shell_cmd(self.cmd)
