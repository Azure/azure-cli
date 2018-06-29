# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps

# pylint: disable=line-too-long

helps['reservations'] = """
    type: group
    short-summary: Manage Azure Reservations.
"""

helps['reservations catalog'] = """
    type: group
    short-summary: See catalog of available reservations
"""

helps['reservations reservation'] = """
    type: group
    short-summary: Manage reservation entities
"""

helps['reservations reservation-order'] = """
    type: group
    short-summary: Manage reservation order, which is container for reservations
"""

helps['reservations reservation-order-id'] = """
    type: group
    short-summary: See reservation order ids that are applied to subscription
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
          short-summary: Id of reservation order to look up
"""

helps['reservations reservation-order-id list'] = """
    type: command
    short-summary: Get list of applicable reservation order ids.
    long-summary: |
        Get applicable reservations that are applied to this subscription.
    parameters:
        - name: --subscription-id
          type: string
          short-summary: Id of the subscription to look up applied reservations
"""

helps['reservations catalog show'] = """
    type: command
    short-summary: Get catalog of available reservation.
    long-summary: |
        Get the regions and skus that are available for RI purchase for the specified Azure subscription.
    parameters:
        - name: --subscription-id
          type: string
          short-summary: Id of the subscription to get the catalog for
        - name: --reserved-resource-type
          type: string
          short-summary: Type of the resource for which the skus should be provided.
"""

helps['reservations reservation list'] = """
    type: command
    short-summary: Get all reservations.
    long-summary: |
        List all reservations within a reservation order.
    parameters:
        - name: --reservation-order-id
          type: string
          short-summary: Id of container reservation order
"""

helps['reservations reservation show'] = """
    type: command
    short-summary: Get details of a reservation.
    parameters:
        - name: --reservation-order-id
          type: string
          short-summary: Order id of reservation to look up
        - name: --reservation-id
          type: string
          short-summary: Reservation id of reservation to look up
"""

helps['reservations reservation update'] = """
    type: command
    short-summary:  Updates the applied scopes of the reservation.
    parameters:
        - name: --reservation-order-id
          type: string
          short-summary: Reservation order id of the reservation to update
        - name: --reservation-id
          type: string
          short-summary: Id of the reservation to update
        - name: --applied-scope-type -t
          type: string
          short-summary: Type of the Applied Scope to update the reservation with
        - name: --applied-scopes -s
          type: string
          short-summary: Subscription that the benefit will be applied. Do not specify if AppliedScopeType is Shared.
        - name: --instance-flexibility -i
          type: string
          short-summary: Type of the Instance Flexibility to update the reservation with
"""

helps['reservations reservation split'] = """
    type: command
    short-summary: Split a reservation.
    parameters:
        - name: --reservation-order-id
          type: string
          short-summary: Reservation order id of the reservation to split
        - name: --reservation-id
          type: string
          short-summary: Reservation id of the reservation to split
        - name: --quantity-1 -1
          type: int
          short-summary: Quantity of the first reservation that will be created from split operation
        - name: --quantity-2 -2
          type: int
          short-summary: Quantity of the second reservation that will be created from split operation
"""

helps['reservations reservation merge'] = """
    type: command
    short-summary: Merge two reservations.
    parameters:
        - name: --reservation-order-id
          type: string
          short-summary: Reservation order id of the reservations to merge
        - name: --reservation-id-1 -1
          type: string
          short-summary: Id of the first reservation to merge
        - name: --reservation-id-2 -2
          type: string
          short-summary: Id of the second reservation to merge
"""

helps['reservations reservation list-history'] = """
    type: command
    short-summary: Get history of a reservation.
    parameters:
        - name: --reservation-order-id
          type: string
          short-summary: Order id of the reservation
        - name: --reservation-id
          type: string
          short-summary: Reservation id of the reservation
"""
