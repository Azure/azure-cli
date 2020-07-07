import os
import re
import sys
from functools import partial

from tox.config.main import Config
from tox.execute.request import shell_cmd

RE_ITEM_REF = re.compile(
    r"""
    (?<!\\)[{]
    (?:(?P<sub_type>[^[:{}]+):)?    # optional sub_type for special rules
    (?P<substitution_value>(?:\[(?P<section>[^,{}]*)\])?(?P<key>[^:,{}]*))  # substitution key
    (?::(?P<default_value>[^{}]*))?   # default value
    [}]
    """,
    re.VERBOSE,
)
BASE_TEST_ENV = "testenv"


def substitute_once(val, conf, name, section_loader):
    # noinspection PyTypeChecker
    return RE_ITEM_REF.sub(partial(_replace_match, conf, name, section_loader), val)


def replace(value, conf, name, section_loader):
    while True:  # substitution found
        expanded = substitute_once(value, conf, name, section_loader)
        if expanded == value:
            break
        value = expanded
    return expanded


def _replace_match(conf: Config, name, section_loader, match):
    groups = match.groupdict()
    sub_type = groups["sub_type"]
    value = groups["substitution_value"]
    if value == "posargs":
        sub_type = value
    if sub_type == "env":
        replace_value = os.environ.get(groups["key"], groups["default_value"])
    elif sub_type == "posargs":
        try:
            replace_value = shell_cmd(sys.argv[sys.argv.index("--") + 1 :])
        except ValueError:
            replace_value = groups["default_value"] or ""
    else:
        key_missing_value = groups["default_value"]
        if sub_type is not None:
            key_missing_value = value
            value = sub_type
        else:
            value = groups["key"]
        section = groups["section"] or name
        # noinspection PyBroadException
        if section not in conf:
            env_conf = section_loader(section)
        else:
            env_conf = conf[section]
        try:
            replace_value = env_conf[value]
        except Exception:
            # noinspection PyBroadException
            try:
                try:
                    if groups["section"] is None:
                        replace_value = conf.core[value]
                    else:
                        raise KeyError
                except KeyError:
                    if key_missing_value is None:
                        raise
                    replace_value = key_missing_value
            except Exception:
                start, end = match.span()
                replace_value = match.string[start:end]
    if replace_value is None:
        return ""
    return str(replace_value)
