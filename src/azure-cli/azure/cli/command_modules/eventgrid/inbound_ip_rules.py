# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import argparse
from knack.util import CLIError

from azure.mgmt.eventgrid.models import (
    InboundIpRule)


# pylint: disable=protected-access
# pylint: disable=too-few-public-methods
class AddInboundIpRule(argparse._AppendAction):
    def __call__(self, parser, namespace, values, option_string=None):
        if len(values) < 2:
            raise CLIError('usage error: --inbound-ip-rules has IP Address in CIDR notation and corresponding Action.')

        ipmask = values[0]
        action = values[1]
        inbound_ip_rule = InboundIpRule(ip_mask=ipmask, action=action)

        if namespace.inbound_ip_rules is None:
            namespace.inbound_ip_rules = []
        namespace.inbound_ip_rules.append(inbound_ip_rule)
