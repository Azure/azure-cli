from configparser import ConfigParser, SectionProxy
from copy import deepcopy
from itertools import chain
from pathlib import Path
from typing import Dict, List, Optional, Set

from tox.config.sets import ConfigSet

from ..api import EnvList, Loader, Source
from .convert import StrConvert
from .factor import filter_for_env, find_envs
from .replace import BASE_TEST_ENV, replace

TEST_ENV_PREFIX = f"{BASE_TEST_ENV}:"


class Ini(Source):
    CORE_PREFIX = "tox"

    def __init__(self, path: Path) -> None:
        self._parser = ConfigParser()
        with path.open() as file_handler:
            self._parser.read_file(file_handler)
        self._path = path
        core = IniLoader(
            section=self._get_section(self.CORE_PREFIX),
            src=self,
            name=None,
            default_base=EnvList([]),
            section_loader=self._get_section,
        )
        super().__init__(core)
        self._envs = {}  # type: Dict[str, IniLoader]

    def __deepcopy__(self, memo):
        # python < 3.7 cannot copy config parser
        result = self.__class__.__new__(self.__class__)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            if k != "_parser":
                value = deepcopy(v, memo=memo)
            else:
                value = v
            setattr(result, k, value)
        return result

    def _get_section(self, key):
        if self._parser.has_section(key):
            return self._parser[key]
        return None

    @property
    def tox_root(self):
        return self._path.parent.absolute()

    def envs(self, core_config):
        seen = set()
        for name in self._discover_tox_envs(core_config):
            if name not in seen:
                seen.add(name)
                yield name

    BASE_ENV_LIST = EnvList([BASE_TEST_ENV])

    def __getitem__(self, item):
        key = f"{TEST_ENV_PREFIX}{item}"
        return self.get_section(key, item)

    def get_section(self, item, name):
        try:
            return self._envs[item]
        except KeyError:
            loader = IniLoader(self._get_section(item), self, name, self.BASE_ENV_LIST, self._get_section)
            self._envs[item] = loader
            return loader

    def _discover_tox_envs(self, core_config):
        explicit = list(core_config["env_list"])
        yield from explicit
        known_factors = None
        for section in self._parser.sections():
            if section.startswith(BASE_TEST_ENV):
                is_base_section = section == BASE_TEST_ENV
                name = BASE_TEST_ENV if is_base_section else section[len(TEST_ENV_PREFIX) :]
                if not is_base_section:
                    yield name
                if known_factors is None:
                    known_factors = set(chain.from_iterable(e.split("-") for e in explicit))
                yield from self._discover_from_section(section, known_factors)

    def _discover_from_section(self, section, known_factors):
        for key in self._parser[section]:
            value = self._parser[section].get(key)
            if value:
                for env in find_envs(value):
                    if env not in known_factors:
                        yield env

    def __repr__(self):
        return "{}(path={})".format(type(self).__name__, self._path)


class IniLoader(Loader, StrConvert):
    """Load from a ini section"""

    def __init__(
        self, section: Optional[SectionProxy], src: Ini, name: Optional[str], default_base: EnvList, section_loader,
    ) -> None:
        super().__init__(name)
        self._section = section  # type:Optional[SectionProxy]
        self._src = src  # type: Ini
        self._default_base = default_base  # type:EnvList
        self._base = []  # type:List[IniLoader]
        self._section_loader = section_loader

    def __deepcopy__(self, memo):
        # python < 3.7 cannot copy config parser
        result = self.__class__.__new__(self.__class__)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            if k != "_section":
                value = deepcopy(v, memo=memo)
            else:
                value = v
            setattr(result, k, value)
        return result

    def setup_with_conf(self, conf: ConfigSet):
        # noinspection PyUnusedLocal
        def load_bases(values, conf_):
            result = []  # type: List[IniLoader]
            for value in values:
                name = value.lstrip(TEST_ENV_PREFIX)
                ini_loader = self._src.get_section(value, name)  # type: IniLoader
                result.append(ini_loader)
            return result

        conf.add_config(
            keys="base",
            of_type=EnvList,
            default=self._default_base,
            desc="inherit missing keys from these sections",
            post_process=load_bases,
        )
        self._base = conf["base"]

    def make_package_conf(self):
        """no inheritance please if this is a packaging env"""
        self._base = []

    def __repr__(self):
        return "{}(section={}, src={!r})".format(
            type(self).__name__, self._section.name if self._section else self.name, self._src,
        )

    def _load_raw(self, key, conf, as_name=None):
        for candidate in self.loaders:
            if as_name is None and candidate.name == "":
                as_name = self.name
            try:
                return candidate._load_raw_from(as_name, conf, key)
            except KeyError:
                continue
        else:
            raise KeyError

    def _load_raw_from(self, as_name, conf, key):
        if as_name is None:
            as_name = self.name
        if self._section is None:
            raise KeyError(key)
        value = self._section[key]
        collapsed_newlines = value.replace("\\\n", "")  # collapse explicit line splits
        replace_executed = replace(collapsed_newlines, conf, as_name, self._section_loader)  # do replacements
        factor_selected = filter_for_env(replace_executed, as_name)  # select matching factors
        # extend factors
        return factor_selected

    def get_value(self, section, key):
        return self._section_loader(section)[key]

    @property
    def loaders(self):
        yield self
        yield from self._base

    def found_keys(self) -> Set[str]:
        result = set()
        for candidate in self.loaders:
            if candidate._section is not None:
                result.update(candidate._section.keys())
        return result

    @property
    def section_name(self):
        if self._section is None:
            return None
        return self._section.name
