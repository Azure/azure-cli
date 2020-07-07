import itertools
import logging
import os
import shutil
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Union, cast

from tox.config.sets import ConfigSet
from tox.execute.api import Execute
from tox.execute.request import ExecuteRequest

from .cache import Cache

if sys.platform == "win32":
    PASS_ENV_ALWAYS = [
        "SYSTEMDRIVE",  # needed for pip6
        "SYSTEMROOT",  # needed for python's crypto module
        "PATHEXT",  # needed for discovering executables
        "COMSPEC",  # needed for distutils cygwin compiler
        "PROCESSOR_ARCHITECTURE",  # platform.machine()
        "USERPROFILE",  # needed for `os.path.expanduser()`
        "MSYSTEM",  # controls paths printed format
        "TEMP",
        "TMP",
    ]
else:
    PASS_ENV_ALWAYS = [
        "TMPDIR",
    ]


class ToxEnv(ABC):
    def __init__(self, conf: ConfigSet, core: ConfigSet, options, executor: Execute):
        self.conf = conf  # type: ConfigSet
        self.core = core  # type:ConfigSet
        self.options = options
        self._executor = executor
        self.register_config()
        self._cache = Cache(self.conf["env_dir"] / ".tox-cache")
        self._paths = []  # type:List[Path]
        self.logger = logging.getLogger(self.conf["env_name"])

    def register_config(self):
        self.conf.add_constant(
            keys=["env_name", "envname"], desc="the name of the tox environment", value=self.conf.name,
        )
        self.conf.add_config(
            keys=["set_env", "setenv"],
            of_type=Dict[str, str],
            default={},
            desc="environment variables to set when running commands in the tox environment",
        )
        self.conf.add_config(
            keys=["pass_env", "passenv"],
            of_type=List[str],
            default={},
            desc="environment variables to pass on to the tox environment",
            post_process=lambda v, _: list(itertools.chain.from_iterable(i.split(" ") for i in v)),
        )
        self.conf.add_config(
            keys=["env_dir", "envdir"],
            of_type=Path,
            default=lambda conf, name: conf.core["work_dir"] / conf[name]["env_name"],
            desc="directory assigned to the tox environment",
        )
        self.conf.add_config(
            keys=["env_tmp_dir", "envtmpdir"],
            of_type=Path,
            default=lambda conf, name: conf.core["work_dir"] / conf[name]["env_name"] / "tmp",
            desc="a folder that is always reset at the start of the run",
        )

    def setup(self) -> None:
        """
        1. env dir exists
        2. contains a runner with the same type
        """
        env_tmp_dir = cast(Path, self.conf["env_tmp_dir"])
        if env_tmp_dir.exists():
            shutil.rmtree(str(env_tmp_dir), ignore_errors=True)
        env_dir = cast(Path, self.conf["env_dir"])
        conf = {"name": self.conf.name, "type": type(self).__name__}
        with self._cache.compare(conf, ToxEnv.__name__) as (eq, old):
            try:
                if eq is True:
                    return
                # if either the name or type changed and already exists start over
                self.clean()
            finally:
                env_dir.mkdir(exist_ok=True, parents=True)

    def clean(self):
        env_dir = self.conf["env_dir"]
        if env_dir.exists():
            logging.info("removing %s", env_dir)
            shutil.rmtree(cast(Path, env_dir))

    @property
    def environment_variables(self) -> Dict[str, str]:
        result = {}  # type:Dict[str, str]
        pass_env = self.conf["pass_env"]  # type: List[str]
        pass_env.extend(PASS_ENV_ALWAYS)

        set_env = self.conf["set_env"]  # type: Dict[str, str]
        for key, value in os.environ.items():
            if key in pass_env:
                result[key] = value
        result.update(set_env)
        result["PATH"] = os.pathsep.join(
            itertools.chain((str(i) for i in self._paths), os.environ.get("PATH", "").split(os.pathsep)),
        )
        return result

    def execute(
        self,
        cmd: Sequence[Union[Path, str]],
        allow_stdin: bool,
        show_on_standard: Optional[bool] = None,
        cwd: Optional[Path] = None,
    ):
        if cwd is None:
            cwd = self.core["tox_root"]
        if show_on_standard is None:
            show_on_standard = self.options.verbosity > 3
        request = ExecuteRequest(cmd, cwd, self.environment_variables, allow_stdin)
        self.logger.warning("run => %s$ %s", request.cwd, request.shell_cmd)
        outcome = self._executor(request=request, show_on_standard=show_on_standard)
        self.logger.info("done => code %d in %s for  %s", outcome.exit_code, outcome.elapsed, outcome.shell_cmd)
        return outcome

    @staticmethod
    @abstractmethod
    def id() -> str:
        raise NotImplementedError
