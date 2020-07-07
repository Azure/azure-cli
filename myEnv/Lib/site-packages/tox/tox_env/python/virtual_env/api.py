import sys
from abc import ABC
from pathlib import Path
from typing import List, Sequence, Union, cast

from packaging.requirements import Requirement

from tox.config.sets import ConfigSet
from tox.execute.api import Outcome
from tox.execute.local_sub_process import LocalSubProcessExecutor

from ..api import Python


class VirtualEnv(Python, ABC):
    def __init__(self, conf: ConfigSet, core: ConfigSet, options):
        super().__init__(conf, core, options, LocalSubProcessExecutor())

    def create_python_env(self):
        core_cmd = self.core_cmd()
        env_dir = cast(Path, self.conf["env_dir"])
        cmd = core_cmd + ("--clear", env_dir)
        result = self.execute(cmd=cmd, allow_stdin=False)
        result.assert_success(self.logger)

    def core_cmd(self):
        core_cmd = (
            sys.executable,
            "-m",
            "virtualenv",
            "--no-download",
            "--python",
            self.py_info.interpreter.system_executable,
        )
        return core_cmd

    def paths(self) -> List[Path]:
        """Paths to add to the executable"""
        # we use the original executable as shims may be somewhere else
        return list({self.py_info.bin_dir, self.py_info.script_dir})

    def python_cache(self):
        base_python = self.py_info.interpreter
        return {"version_info": list(base_python.version_info), "executable": base_python.executable}

    def install_python_packages(
        self, packages: List[Union[Requirement, Path]], no_deps: bool = False, develop=False, force_reinstall=False,
    ) -> None:
        if packages:
            install_command = self.install_command(develop, force_reinstall, no_deps, packages)
            result = self.perform_install(install_command)
            result.assert_success(self.logger)

    def perform_install(self, install_command: Sequence[str]) -> Outcome:
        return self.execute(cmd=install_command, allow_stdin=False)

    # noinspection PyMethodMayBeStatic
    def install_command(self, develop, force_reinstall, no_deps, packages):
        install_command = ["python", "-m", "pip", "--disable-pip-version-check", "install"]
        if develop is True:
            install_command.append("-e")
        if no_deps:
            install_command.append("--no-deps")
        if force_reinstall:
            install_command.append("--force-reinstall")
        install_command.extend(str(i) for i in packages)
        return install_command
