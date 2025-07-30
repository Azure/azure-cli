# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=protected-access

import argparse
import json
from argparse import OPTIONAL
from azure.cli.core.azclierror import InvalidArgumentValueError, CLIInternalError
from knack.util import CLIError


# pylint: disable=too-few-public-methods
class _AppendToDictionaryAction(argparse.Action):

    def __init__(self,
                 option_strings,
                 dest,
                 nargs=None,
                 const=None,
                 default=None,
                 type=None,  # pylint: disable=W0622
                 choices=None,
                 required=False,
                 help=None,  # pylint: disable=W0622
                 metavar=None):
        if nargs == 0:
            raise ValueError('nargs for append actions must be > 0; if arg '
                             'strings are not supplying the value to append, '
                             'the append const action may be more appropriate')
        if const is not None and nargs != OPTIONAL:
            raise ValueError('nargs must be %r to supply const' % OPTIONAL)
        super().__init__(
            option_strings=option_strings,
            dest=dest,
            nargs=nargs,
            const=const,
            default=default,
            type=type,
            choices=choices,
            required=required,
            help=help,
            metavar=metavar)

    def __call__(self, parser, namespace, values, option_string=None):
        items = getattr(namespace, self.dest, None)
        if items is None:
            items = {}
        key = values[0]
        value = values[1]
        if key in items:
            items[key].append(value)
        else:
            items[key] = []
            items[key].append(value)
        setattr(namespace, self.dest, items)


# pylint: disable=protected-access, too-few-public-methods
class AppendBaseline(argparse._AppendAction):

    def __call__(self, parser, namespace, values, option_string=None):
        try:
            super().__call__(parser, namespace, values, option_string)
        except ValueError:
            raise CLIInternalError("Unexpected error")


# pylint: disable=protected-access, too-few-public-methods
class AppendBaselines(_AppendToDictionaryAction):

    def __call__(self, parser, namespace, values, option_string=None):
        try:
            rule_id = _get_rule_id(values[0])
            baseline_row_values = values[1:]
            super().__call__(parser, namespace, (rule_id, baseline_row_values), option_string)
        except ValueError:
            raise CLIInternalError("Unexpected error")


def _get_rule_id(rule_param):
    try:
        split_result = rule_param.split("=")
        if len(split_result) != 2 or split_result[0] != "rule":
            raise InvalidArgumentValueError("Invalid baseline format. Use help for examples")
        return split_result[1]
    except:
        raise InvalidArgumentValueError("Invalid baseline format. Use help for examples")


class GetExtension(argparse._AppendAction):

    def __call__(self, parser, namespace, values, option_string=None):
        action = self.get_action(values, option_string)
        super().__call__(parser, namespace, action, option_string)

    def get_action(self, values, option_string):  # pylint: disable=no-self-use
        try:
            properties = {}
            for (k, v) in (x.split('=', 1) for x in values):
                if k == "isEnabled":
                    properties["is_enabled"] = v
                elif k == "name":
                    properties["name"] = v
                elif k == "additionalExtensionProperties":
                    try:
                        properties["additional_extension_properties"] = json.loads(v)
                    except Exception:
                        msg = "usage error: make sure that additionalExtensionProperties is valid escaped JSON," \
                              " use online tools to escape the JSON"
                        raise CLIError(msg)
            return dict(properties)
        except ValueError:
            raise CLIError('usage error: {} [KEY=VALUE ...]'.format(option_string))
