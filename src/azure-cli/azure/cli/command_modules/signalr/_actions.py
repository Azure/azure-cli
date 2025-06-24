# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

import argparse
from azure.mgmt.signalr.models import UpstreamTemplate, IPRule
from azure.cli.core.azclierror import InvalidArgumentValueError
from knack.log import get_logger
from knack.util import CLIError

logger = get_logger(__name__)


# pylint: disable=protected-access, too-few-public-methods
class UpstreamTemplateAddAction(argparse._AppendAction):
    def __call__(self, parser, namespace, values, option_string=None):
        kwargs = {}
        for item in values:
            try:
                key, value = item.split('=', 1)
                kwargs[key.replace('-', '_')] = value
            except ValueError:
                raise CLIError('usage error: {} KEY=VALUE [KEY=VALUE ...]'.format(option_string))
        value = UpstreamTemplate(**kwargs)
        super().__call__(parser, namespace, value, option_string)


class IPRuleTemplateUpdateAction(argparse._AppendAction):
    # --ip-rule value="" action=""
    def __call__(self, parser, namespace, values, option_string=None):
        ipRuleValue = None
        ipRuleAction = None
        for item in values:
            try:
                key, value = item.split('=', 1)
                if key == 'value':
                    ipRuleValue = value
                elif key == 'action':
                    ipRuleAction = value
                else:
                    raise InvalidArgumentValueError('usage error: {} KEY=VALUE [KEY=VALUE ...]'.format(option_string))
            except ValueError:
                raise InvalidArgumentValueError('usage error: {} KEY=VALUE [KEY=VALUE ...]'.format(option_string))
        if ipRuleValue is None or ipRuleAction is None:
            raise InvalidArgumentValueError('usage error: {} KEY=VALUE [KEY=VALUE ...]'.format(option_string))
        value = IPRule(value=ipRuleValue, action=ipRuleAction)
        super().__call__(parser, namespace, value, option_string)
