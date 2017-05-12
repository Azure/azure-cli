# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import argparse
import re

from azure.cli.core.util import CLIError
from azure.cli.command_modules.monitor.custom import operator_map, aggregation_map

def period_type(value):

    def _get_substring(range):
        if range == tuple([-1, -1]):
            return ''
        else:
            return value[range[0]: range[1]]

    regex = '(p)?(\d+y)?(\d+m)?(\d+d)?(t)?(\d+h)?(\d+m)?(\d+s)?'
    match = re.match(regex, value.lower())
    match_len = match.regs[0]
    if match_len != tuple([0, len(value)]):
        raise ValueError
    # simply return value if a valid ISO8601 string is supplied
    if match.regs[1] != tuple([-1, -1]) and match.regs[5] != tuple([-1, -1]):
        return value
    else:
        # if shorthand is used, only support days, minutes, hours, seconds
        days = _get_substring(match.regs[4])
        minutes = _get_substring(match.regs[6])
        hours = _get_substring(match.regs[7])
        seconds = _get_substring(match.regs[8])
        return 'P{}T{}{}{}'.format(days, minutes, hours, seconds).upper()

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


class WebhookAction(argparse._AppendAction):
    def __call__(self, parser, namespace, values, option_string=None):
        webhook_action = self.get_webhook(values, option_string)
        super(WebhookAction, self).__call__(parser, namespace, webhook_action, option_string)

    def get_webhook(self, values, option_string):
        from azure.mgmt.monitor.models import RuleWebhookAction
        uri = values[0]
        try:
            properties = dict(x.split('=', 1) for x in values[1:])
        except ValueError:
            raise CLIError('usage error: --webhook URI [KEY=VALUE ...]')
        webhook_action = RuleWebhookAction(uri, properties)
        return webhook_action
