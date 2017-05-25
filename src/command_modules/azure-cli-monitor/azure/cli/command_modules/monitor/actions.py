# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import argparse
import re

from azure.cli.core.util import CLIError
from azure.cli.command_modules.monitor.custom import operator_map, aggregation_map


def period_type(value):

    def _get_substring(indices):
        if indices == tuple([-1, -1]):
            return ''
        return value[indices[0]: indices[1]]

    regex = r'(p)?(\d+y)?(\d+m)?(\d+d)?(t)?(\d+h)?(\d+m)?(\d+s)?'
    match = re.match(regex, value.lower())
    match_len = match.regs[0]
    if match_len != tuple([0, len(value)]):
        raise ValueError
    # simply return value if a valid ISO8601 string is supplied
    if match.regs[1] != tuple([-1, -1]) and match.regs[5] != tuple([-1, -1]):
        return value

    # if shorthand is used, only support days, minutes, hours, seconds
    # ensure M is interpretted as minutes
    days = _get_substring(match.regs[4])
    minutes = _get_substring(match.regs[6]) or _get_substring(match.regs[3])
    hours = _get_substring(match.regs[7])
    seconds = _get_substring(match.regs[8])
    return 'P{}T{}{}{}'.format(days, minutes, hours, seconds).upper()


# pylint: disable=too-few-public-methods
class ConditionAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        from azure.mgmt.monitor.models import ThresholdRuleCondition, RuleMetricDataSource
        # get default description if not specified
        if namespace.description is None:
            namespace.description = ' '.join(values)
        if len(values) == 1:
            # workaround because CMD.exe eats > character... Allows condition to be
            # specified as a quoted expression
            values = values[0].split(' ')
        if len(values) < 5:
            raise CLIError('usage error: --condition METRIC {>,>=,<,<=} THRESHOLD {avg,min,max,total,last} DURATION')
        metric_name = ' '.join(values[:-4])
        operator = operator_map[values[-4]]
        threshold = int(values[-3])
        aggregation = aggregation_map[values[-2].lower()]
        window = period_type(values[-1])
        metric = RuleMetricDataSource(None, metric_name)  # target URI will be filled in later
        condition = ThresholdRuleCondition(operator, threshold, metric, window, aggregation)
        namespace.condition = condition


# pylint: disable=protected-access
class AlertAddAction(argparse._AppendAction):
    def __call__(self, parser, namespace, values, option_string=None):
        action = self.get_action(values, option_string)
        super(AlertAddAction, self).__call__(parser, namespace, action, option_string)

    def get_action(self, values, option_string):  # pylint: disable=no-self-use
        _type = values[0].lower()
        if _type == 'email':
            from azure.mgmt.monitor.models import RuleEmailAction
            return RuleEmailAction(custom_emails=values[1:])
        elif _type == 'webhook':
            from azure.mgmt.monitor.models import RuleWebhookAction
            uri = values[1]
            try:
                properties = dict(x.split('=', 1) for x in values[2:])
            except ValueError:
                raise CLIError('usage error: {} webhook URI [KEY=VALUE ...]'.format(option_string))
            return RuleWebhookAction(uri, properties)

        raise CLIError('usage error: {} TYPE KEY [ARGS]'.format(option_string))


class AlertRemoveAction(argparse._AppendAction):
    def __call__(self, parser, namespace, values, option_string=None):
        action = self.get_action(values, option_string)
        super(AlertRemoveAction, self).__call__(parser, namespace, action, option_string)

    def get_action(self, values, option_string):  # pylint: disable=no-self-use
        # TYPE is artificially enforced to create consistency with the --add-action argument
        # but it could be enhanced to do additional validation in the future.
        _type = values[0].lower()
        if _type not in ['email', 'webhook']:
            raise CLIError('usage error: {} TYPE KEY [KEY ...]'.format(option_string))
        return values[1:]
