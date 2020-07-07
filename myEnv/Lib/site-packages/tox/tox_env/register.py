from typing import Dict, Iterable, Type

from .package import PackageToxEnv
from .runner import RunToxEnv


class ToxEnvRegister:
    def __init__(self):
        self._run_envs = {}  # type:Dict[str, Type[RunToxEnv]]
        self._package_envs = {}  # type:Dict[str, Type[PackageToxEnv]]
        self._default_run_env = ""  # type:str

    def populate(self, manager):
        manager.tox_register_tox_env(register=self)
        self._default_run_env = next(iter(self._run_envs.keys()))  # type:str

    def add_run_env(self, of_type: Type[RunToxEnv]):
        self._run_envs[of_type.id()] = of_type

    def add_package_env(self, of_type: Type[PackageToxEnv]):
        self._package_envs[of_type.id()] = of_type

    @property
    def run_envs(self) -> Iterable[str]:
        return self._run_envs.keys()

    @property
    def default_run_env(self) -> str:
        return self._default_run_env

    @default_run_env.setter
    def default_run_env(self, value: str) -> None:
        assert value in self._run_envs, "default env must be in run envs"
        self._default_run_env = value

    def runner(self, name: str) -> Type[RunToxEnv]:
        return self._run_envs[name]

    def package(self, name: str) -> Type[PackageToxEnv]:
        return self._package_envs[name]


REGISTER = ToxEnvRegister()
