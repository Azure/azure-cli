# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# coding: utf-8
# pylint: skip-file
from msrest.serialization import Model


class SharedPublicIpAddressConfigurationFragment(Model):
    """Properties of a virtual machine that determine how it is connected to a
    load balancer.

    :param inbound_nat_rules: The incoming NAT rules
    :type inbound_nat_rules: list of :class:`InboundNatRuleFragment
     <devtestlabs.models.InboundNatRuleFragment>`
    """

    _attribute_map = {
        'inbound_nat_rules': {'key': 'inboundNatRules', 'type': '[InboundNatRuleFragment]'},
    }

    def __init__(self, inbound_nat_rules=None):
        self.inbound_nat_rules = inbound_nat_rules
