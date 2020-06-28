import shlex
from itertools import chain
from pathlib import Path

from tox.config.source.api import Command, Convert, EnvList


class StrConvert(Convert):
    @staticmethod
    def to_path(value):
        return Path(value)

    @staticmethod
    def to_list(value):
        splitter = "\n" if "\n" in value else ","
        for token in value.split(splitter):
            value = token.strip()
            if value:
                yield value

    @staticmethod
    def to_set(value):
        return set(StrConvert.to_list(value))

    @staticmethod
    def to_dict(value):
        for row in value.split("\n"):
            row = row.strip()
            if row:
                try:
                    at = row.index("=")
                except ValueError:
                    raise TypeError(f"dictionary lines must be of form key=value, found {row}")
                else:
                    key = row[:at].strip()
                    value = row[at + 1 :].strip()
                    yield key, value

    @staticmethod
    def to_command(value):
        return Command(shlex.split(value))

    @staticmethod
    def to_env_list(value):
        from tox.config.source.ini.factor import extend_factors

        elements = list(chain.from_iterable(extend_factors(expr) for expr in value.split("\n")))
        return EnvList(elements)

    TRUTHFUL_VALUES = {"true", "1", "yes", "on"}
    FALSY_VALUES = {"false", "0", "no", "off"}
    VALID_BOOL = list(sorted(TRUTHFUL_VALUES | FALSY_VALUES))

    @staticmethod
    def to_bool(value):
        norm = value.strip().lower()
        if norm in StrConvert.TRUTHFUL_VALUES:
            return True
        elif norm in StrConvert.FALSY_VALUES:
            return False
        else:
            raise TypeError(
                "value {} cannot be transformed to bool, valid: {}".format(value, ", ".join(StrConvert.VALID_BOOL)),
            )
