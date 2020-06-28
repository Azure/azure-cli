from abc import ABC, abstractmethod
from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, List, Sequence, Set, Union

from tox.execute.request import shell_cmd

_NO_MAPPING = object()


class Command:
    def __init__(self, args):
        self.args = args  # type:List[str]

    def __repr__(self):
        return "{}(args={!r})".format(type(self).__name__, self.args)

    def __eq__(self, other):
        return type(self) == type(other) and self.args == other.args

    @property
    def shell(self):
        return shell_cmd(self.args)


class EnvList:
    def __init__(self, envs: Sequence[str]):
        self.envs = list(OrderedDict((e, None) for e in envs).keys())

    def __repr__(self):
        return "{}(envs={!r})".format(type(self).__name__, ",".join(self.envs))

    def __eq__(self, other):
        return type(self) == type(other) and self.envs == other.envs

    def __iter__(self):
        return iter(self.envs)


class Convert(ABC):
    def to(self, raw, of_type):
        if getattr(of_type, "__module__", None) == "typing":
            return self._to_typing(raw, of_type)
        elif issubclass(of_type, Path):
            return self.to_path(raw)
        elif issubclass(of_type, bool):
            return self.to_bool(raw)
        elif issubclass(of_type, Command):
            return self.to_command(raw)
        elif issubclass(of_type, EnvList):
            return self.to_env_list(raw)
        elif issubclass(of_type, str):
            return self.to_str(raw)
        return of_type(raw)

    def _to_typing(self, raw, of_type):
        origin = getattr(of_type, "__origin__", None)
        if origin is not None:
            result = _NO_MAPPING  # type: Any
            if origin in (list, List):
                result = [self.to(i, of_type.__args__[0]) for i in self.to_list(raw)]
            elif origin in (set, Set):
                result = {self.to(i, of_type.__args__[0]) for i in self.to_set(raw)}
            elif origin in (dict, Dict):
                result = OrderedDict(
                    (self.to(k, of_type.__args__[0]), self.to(v, of_type.__args__[1])) for k, v in self.to_dict(raw)
                )
            elif origin == Union:
                if len(of_type.__args__) == 2 and type(None) in of_type.__args__:
                    if not raw.strip():
                        result = None
                    else:
                        new_type = next(i for i in of_type.__args__ if i != type(None))  # noqa
                        result = self._to_typing(raw, new_type)
            if result is not _NO_MAPPING:
                return result
        raise TypeError(f"{raw} cannot cast to {of_type!r}")

    @staticmethod
    def to_str(value):
        return value.strip()

    @staticmethod
    @abstractmethod
    def to_list(value):
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def to_set(value):
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def to_dict(value):
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def to_path(value):
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def to_command(value):
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def to_env_list(value):
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def to_bool(value):
        raise NotImplementedError


class Loader(Convert, ABC):
    """Loader is able to load a given key of given type from a source. Each source will have its own loader."""

    def __init__(self, name):
        self.name = name

    def load(self, key, of_type, conf):
        raw = self._load_raw(key, conf)
        converted = self.to(raw, of_type)
        return converted

    @abstractmethod
    def setup_with_conf(self, conf):
        raise NotImplementedError

    def make_package_conf(self):
        """"""

    @abstractmethod
    def _load_raw(self, key, conf):
        raise NotImplementedError

    @abstractmethod
    def found_keys(self) -> Set[str]:
        raise NotImplementedError


class Source(ABC):
    def __init__(self, core: Loader) -> None:
        self.core = core  # type: Loader
        self._envs = {}  # type: Dict[str, Loader]

    @abstractmethod
    def envs(self, core_conf):
        raise NotImplementedError

    @abstractmethod
    def __getitem__(self, item):
        raise NotImplementedError

    @property
    @abstractmethod
    def tox_root(self):
        raise NotImplementedError
