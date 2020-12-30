# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=protected-access

import argparse
from collections import defaultdict
from azure.cli.core.azclierror import InvalidArgumentValueError


# pylint: disable=protected-access
class AppendBaselineLines(argparse._AppendAction):

    def __call__(self, parser, namespace, values, option_string=None):
        try:
            super(AppendBaselineLines, self).__call__(parser, namespace, values, option_string)
        except ValueError:
            raise CLIError("Unexpected error")


class _AppendToDictionaryAction(argparse.Action):

    def __init__(self,
                 option_strings,
                 dest,
                 nargs=None,
                 const=None,
                 default=None,
                 type=None,
                 choices=None,
                 required=False,
                 help=None,
                 metavar=None):
        if nargs == 0:
            raise ValueError('nargs for append actions must be > 0; if arg '
                             'strings are not supplying the value to append, '
                             'the append const action may be more appropriate')
        if const is not None and nargs != OPTIONAL:
            raise ValueError('nargs must be %r to supply const' % OPTIONAL)
        super(_AppendToDictionaryAction, self).__init__(
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
        items = _copy_items_to_dict(items)
        key = values[0]
        value = values[1]
        if key in items:
            items[key].append(value)
        else:
            items[key] = list()
            items[key].append(value)
        setattr(namespace, self.dest, items)


def _copy_items_to_dict(items):
    if items is None:
        return dict()
    if type(items) is dict:
        return items
    raise CLIInternalError("Unexpected error")


# pylint: disable=protected-access
class AppendBaselines(_AppendToDictionaryAction):

    def __init__(self, option_strings, dest, nargs=None, const=None, default=None, type=None, choices=None, required=False, help=None, metavar=None):
        super(AppendBaselines, self).__init__(option_strings, dest, nargs, const, default, type, choices, required, help, metavar)

    def __call__(self, parser, namespace, values, option_string=None):
        try:
            rule_id = _get_rule_id(values[0])
            baseline_row_values = values[1:]
            super(AppendBaselines, self).__call__(parser, namespace, (rule_id, baseline_row_values), option_string)
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
