# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps

# pylint: disable=line-too-long, too-many-lines

helps['network nat-gateway'] = """
    type: group
    short-summary: Manage NAT gateways.
"""

helps['network nat-gateway create'] = """
    type: command
    short-summary: Create NAT Gateways
    parameters:
      - name: --name
        short-summary: Name of the Nat Gateway.
      - name: --public-ip-addresses
        short-summary: Space seperated list of Public Ip Addresses.
      - name: --public-ip-prefixes
        short-summary: Space seperated list of Public Ip Prefixes.
      - name: --idle-timeout
        short-summary: Idle Timeout in minutes.
"""

helps['network nat-gateway delete'] = """
    type: command
    short-summary: Delete NAT gateways.
"""

helps['network nat-gateway list'] = """
    type: command
    short-summary: List NAT gateways.
"""

helps['network nat-gateway show'] = """
    type: command
    short-summary: Show NAT gateways.
    parameters:
      - name: --name
        short-summary: Name of the Nat Gateway.
"""

helps['network nat-gateway update'] = """
    type: command
    short-summary: Update NAT gateways.
    parameters:
      - name: --name
        short-summary: Name of the Nat Gateway.
      - name: --public-ip-addresses
        short-summary: Space seperated list of Public Ip Addresses.
      - name: --public-ip-prefixes
        short-summary: Space seperated list of Public Ip Prefixes.
      - name: --idle-timeout
        short-summary: Idle Timeout in minutes.
"""

helps['network nat-gateway wait'] = """
    type: command
    short-summary: Wait for Nat Gateway to be created.
"""
