from abc import ABC, abstractmethod
from collections import OrderedDict
from copy import deepcopy
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Iterable,
    Optional,
    Sequence,
    Set,
    Type,
    Union,
)

from tox.config.source.api import Loader

if TYPE_CHECKING:
    from tox.config.main import Config  # pragma: no cover


class ConfigDefinition(ABC):
    def __init__(self, keys: Iterable[str], desc: str) -> None:
        self.keys = keys
        self.desc = desc

    @abstractmethod
    def __call__(self, src: Loader, conf: "Config"):
        raise NotImplementedError


class ConfigConstantDefinition(ConfigDefinition):
    def __init__(self, keys: Iterable[str], desc: str, value: Any) -> None:
        super().__init__(keys, desc)
        self.value = value

    def __call__(self, src: Loader, conf: "Config"):
        if callable(self.value):
            value = self.value()
        else:
            value = self.value
        return value


_PLACE_HOLDER = object()


class ConfigDynamicDefinition(ConfigDefinition):
    def __init__(
        self,
        keys: Iterable[str],
        of_type: Union[Type, str],
        default: Any,
        desc: str,
        post_process: Optional[Callable[[str], Any]] = None,
    ) -> None:
        super().__init__(keys, desc)
        self.of_type = of_type
        self.default = default
        self.post_process = post_process
        self._cache = _PLACE_HOLDER

    def __call__(self, src: Loader, conf: "Config"):
        if self._cache is _PLACE_HOLDER:
            for key in self.keys:
                try:
                    value = src.load(key, self.of_type, conf)
                except KeyError:
                    continue
                break
            else:
                value = self.default(conf, src.name) if callable(self.default) else self.default
            if self.post_process is not None:
                value = self.post_process(value, conf)
            self._cache = value
        return self._cache

    def __deepcopy__(self, memo):
        # we should not copy the place holder as our checks would break
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            if k != "_cache" and v is _PLACE_HOLDER:
                value = deepcopy(v, memo=memo)
            else:
                value = v
            setattr(result, k, value)
        return result

    def __repr__(self):
        return "{}(keys={!r}, of_type={!r}, default={!r}, desc={!r}, post_process={!r})".format(
            type(self).__name__, self.keys, self.of_type, self.default, self.desc, self.post_process,
        )


class ConfigSet:
    def __init__(self, raw: Loader, conf: "Config"):
        self._raw = raw
        self._defined = {}  # type:Dict[str, ConfigDefinition]
        self._conf = conf
        self._keys = OrderedDict()
        self._raw.setup_with_conf(self)

    def add_config(
        self,
        keys: Union[str, Sequence[str]],
        of_type: Union[Type, str],
        default: Any,
        desc: str,
        post_process=None,
        overwrite=False,
    ):
        """
        Add configuration.

        :param keys:
        :param of_type:
        :param default:
        :param desc:
        :param post_process:
        :param overwrite:
        :return:
        """
        keys_ = self._make_keys(keys)
        for key in keys_:
            if key in self._defined and overwrite is False:
                # already added
                return
        definition = ConfigDynamicDefinition(keys_, of_type, default, desc, post_process)
        self._add_conf(keys_, definition)

    def add_constant(self, keys, desc, value):
        keys_ = self._make_keys(keys)
        definition = ConfigConstantDefinition(keys_, desc, value)
        self._add_conf(keys, definition)

    def make_package_conf(self):
        self._raw.make_package_conf()

    @staticmethod
    def _make_keys(keys):
        return (keys,) if isinstance(keys, str) else keys

    def _add_conf(self, keys: Union[str, Sequence[str]], definition: ConfigDefinition):
        self._keys[keys[0]] = None
        for key in keys:
            self._defined[key] = definition

    @property
    def name(self):
        return self._raw.name

    def __getitem__(self, item):
        return self._defined[item](self._raw, self._conf)

    def __repr__(self):
        return "{}(raw={!r}, conf={!r})".format(type(self).__name__, self._raw, self._conf)

    def __iter__(self):
        return iter(self._keys.keys())

    def unused(self) -> Set[str]:
        return self._raw.found_keys() - set(self._defined.keys())
