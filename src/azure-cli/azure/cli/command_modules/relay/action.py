# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
# pylint: disable=inconsistent-return-statements
# pylint: disable=protected-access

import argparse


class AlertAddIpRule(argparse._AppendAction):
    def __call__(self, parser, namespace, values, option_string=None):
        action = self.get_action(values, option_string)
        super().__call__(parser, namespace, action, option_string)

    def get_action(self, values, option_string):  # pylint: disable=no-self-use
        from azure.cli.core import CLIError
        from azure.cli.core.azclierror import InvalidArgumentValueError
        IpRuleList = {}
        for (k, v) in (x.split('=', 1) for x in values):
            if k == 'ip-address':
                IpRuleList["ip-address"] = v
            elif k == 'action':
                IpRuleList["action"] = v
            else:
                raise InvalidArgumentValueError(
                    "Invalid Argument for:'{}' Only allowed arguments are 'ip-address, action'".format(option_string))

        if IpRuleList["ip-address"] is None:
            raise CLIError('ip-address is mandatory properties')

        if "action" not in IpRuleList:
            IpRuleList["action"] = 'Allow'
        return IpRuleList
