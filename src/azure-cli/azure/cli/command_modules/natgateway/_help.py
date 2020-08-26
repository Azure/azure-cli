# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps  # pylint: disable=unused-import
# pylint: disable=line-too-long, too-many-lines

helps['network nat'] = """
type: group
short-summary: Commands to manage NAT resources.
"""

helps['network nat gateway'] = """
type: group
short-summary: Commands to manage NAT gateways.
"""

helps['network nat gateway create'] = """
type: command
short-summary: Create a NAT gateway.
examples:
  - name: Create a NAT gateway.
    text: az network nat gateway create --resource-group MyResourceGroup --name MyNatGateway --location MyLocation --public-ip-addresses  MyPublicIp --public-ip-prefixes  MyPublicIpPrefix --idle-timeout 4 --zone 2
"""

helps['network nat gateway delete'] = """
type: command
short-summary: Delete a NAT gateway.
examples:
  - name: Delete a NAT gateway.
    text: az network nat gateway delete --resource-group MyResourceGroup --name MyNatGateway
"""

helps['network nat gateway list'] = """
type: command
short-summary: List NAT gateways.
examples:
  - name: List NAT gateways.
    text: az network nat gateway list -g MyResourceGroup
"""

helps['network nat gateway show'] = """
type: command
short-summary: Show details of a NAT gateway.
examples:
  - name: Show details of a NAT gateway.
    text: az network nat gateway show --resource-group MyResourceGroup --name MyNatGateway
  - name: Show NAT gateway using ID.
    text: az network nat gateway show --ids {GatewayId}
"""

helps['network nat gateway update'] = """
type: command
short-summary: Update a NAT gateway.
examples:
  - name: Update a NAT gateway.
    text: az network nat gateway update -g MyResourceGroup --name MyNatGateway --idle-timeout 5
"""

helps['network nat gateway wait'] = """
type: command
short-summary: Place the CLI in a waiting state until a condition of the NAT gateway is met.
"""
