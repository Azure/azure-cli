# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.help_files import helps
# pylint: disable=line-too-long

helps['reservations'] = """
    type: group
    short-summary: Manage Azure Reservations.
"""

helps['reservations reservation-order list'] = """
    type: command
    short-summary: Get all reservation orders
    long-summary: |
        List of all the reservation orders that the user has access to in the current tenant.
"""

helps['reservations reservation-order show'] = """
    type: command
    short-summary: Get a specific reservation order.
    long-summary: Get the details of the reservation order.
    parameters:
        - name: --reservation-order-id
          type: string
"""

helps['reservations reservation-order-id list'] = """
    type: command
    short-summary: Get list of applicable reservation order ids.
    long-summary: |
        Get applicable reservations that are applied to this subscription.
    parameters:
        - name: --subscription-id
          type: string
"""

helps['reservations catalog show'] = """
    type: command
    short-summary: Get catalog of available reservation.
    long-summary: |
        Get the regions and skus that are available for RI purchase for the specified Azure subscription.
    parameters:
        - name: --subscription-id
          type: string
"""

helps['reservations reservation list'] = """
    type: command
    short-summary: Get all reservations.
    long-summary: |
        List all reservations within a reservation order.
    parameters:
        - name: --reservation-order-id
          type: string
"""

helps['reservations reservation show'] = """
    type: command
    short-summary: Get details of a reservation.
    parameters:
        - name: --reservation-order-id
          type: string
        - name: --reservation-id
          type: string
"""

helps['reservations reservation update'] = """
    type: command
    short-summary:  Updates the applied scopes of the reservation.
    parameters:
        - name: --reservation-order-id
          type: string
        - name: --reservation-id
          type: string
        - name: --applied-scope-type -t
          type: string
          short-summary: 'Type is either Single or Shared'
        - name: --applied-scopes -s
          type: string
          short-summary: 'If applied scope type is Single, this field must be provided'
"""

helps['reservations reservation split'] = """
    type: command
    short-summary: Split a reservation.
    parameters:
        - name: --reservation-order-id
          type: string
        - name: --reservation-id
          type: string
        - name: --quantity-1 -1
          type: int
        - name: --quantity-2 -2
          type: int
"""

helps['reservations reservation merge'] = """
    type: command
    short-summary: Merge two reservations.
    parameters:
        - name: --reservation-order-id
          type: string
        - name: --reservation-id-1 -1
          type: string
        - name: --reservation-id-2 -2
          type: string
"""

helps['reservations reservation list-history'] = """
    type: command
    short-summary: Get history of a reservation.
    parameters:
        - name: --reservation-order-id
          type: string
        - name: --reservation-id-1 -1
          type: string
        - name: --reservation-id-2 -2
          type: string
"""
