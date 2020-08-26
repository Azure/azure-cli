# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import argparse

from knack.util import CLIError


# pylint:disable=protected-access
# pylint:disable=too-few-public-methods
class OriginType(argparse._AppendAction):
    def __call__(self, parser, namespace, values, option_string=None):
        deep_created_origin = self.get_origin(values, option_string)
        super(OriginType, self).__call__(parser, namespace, deep_created_origin, option_string)

    def get_origin(self, values, option_string):
        from azure.mgmt.cdn.models import DeepCreatedOrigin

        if not 1 <= len(values) <= 3 and not 5 <= len(values) <= 6:
            msg = '%s takes 1, 2, 3, 5, or 6 values, %d given'
            raise argparse.ArgumentError(
                self, msg % (option_string, len(values)))

        deep_created_origin = DeepCreatedOrigin(
            name='origin',
            host_name=values[0],
            http_port=80,
            https_port=443)

        if len(values) > 1:
            deep_created_origin.http_port = int(values[1])
        if len(values) > 2:
            deep_created_origin.https_port = int(values[2])
        if len(values) > 4:
            deep_created_origin.private_link_resource_id = values[3]
            deep_created_origin.private_link_location = values[4]
        if len(values) > 5:
            deep_created_origin.private_link_approval_message = values[5]
        return deep_created_origin


# pylint: disable=protected-access
# pylint:disable=too-few-public-methods
class MatchConditionAction(argparse._AppendAction):

    def __call__(self, parser, namespace, values, option_string=None):
        match_condition = get_match_condition(values, option_string)
        super(MatchConditionAction, self).__call__(parser, namespace, match_condition, option_string)


def get_match_condition(values, option_string):
    from azure.mgmt.cdn.models import MatchCondition

    match_values = []
    match_variable = None
    negate_condition = None
    operator = None
    selector = None
    transforms = []
    for item in values:
        if '=' not in item:
            raise CLIError('usage error: {} KEY=VALUE [KEY=VALUE ...]'.format(option_string))
        key, value = item.split('=', 1)
        key = key.lower()

        if key == "match-value":
            match_values.append(value)
        elif key == "transform":
            transforms.append(value)
        elif key == "match-variable":
            if match_variable is not None:
                raise CLIError('usage error: match-variable may only be specified once per match condition.')
            match_variable = value
        elif key == "negate":
            if negate_condition is not None:
                raise CLIError('usage error: negate may only be specified once per match condition.')
            negate_condition = value.lower() == "true"
        elif key == "operator":
            if operator is not None:
                raise CLIError('usage error: operator may only be specified once per match condition.')
            operator = value
        elif key == "selector":
            if selector is not None:
                raise CLIError('usage error: selector may only be specified once per match condition.')
            selector = value
        else:
            raise CLIError('usage error: unrecognized key {}'.format(key))
    return MatchCondition(match_variable=match_variable,
                          match_value=match_values,
                          negate_condition=negate_condition,
                          operator=operator,
                          selector=selector,
                          transforms=transforms)


# pylint: disable=protected-access
# pylint:disable=too-few-public-methods
class ManagedRuleOverrideAction(argparse._AppendAction):

    def __call__(self, parser, namespace, values, option_string=None):
        rule_override = get_rule_override(values, option_string)
        super(ManagedRuleOverrideAction, self).__call__(parser, namespace, rule_override, option_string)


def get_rule_override(values, option_string):
    from azure.mgmt.cdn.models import ManagedRuleOverride

    rule_id = None
    action = None
    enabled = None

    for item in values:
        if '=' not in item:
            raise CLIError('usage error: {} KEY=VALUE [KEY=VALUE ...]'.format(option_string))
        key, value = item.split('=', 1)
        key = key.lower()

        if key == "id":
            if rule_id is not None:
                raise CLIError('usage error: id may only be specified once per rule override.')
            rule_id = value
        elif key == "action":
            if action is not None:
                raise CLIError('usage error: action may only be specified once per rule override.')
            action = value
        elif key == "enabled":
            if enabled is not None:
                raise CLIError('usage error: enabled may only be specified once per rule override.')
            enabled = value
        else:
            raise CLIError('usage error: unrecognized key {}'.format(key))
    return ManagedRuleOverride(rule_id=rule_id,
                               action=action,
                               enabled_state=enabled)
