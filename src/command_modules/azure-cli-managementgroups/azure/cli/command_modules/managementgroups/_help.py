# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps

# pylint: disable=line-too-long, too-many-lines

helps['managementgroups'] = """
    type: group
    short-summary: Manage Azure Management Groups.
"""
helps['managementgroups group'] = """
    type: group
    short-summary: Group operations for Management Groups.
"""

helps['managementgroups subscription'] = """
    type: group
    short-summary: Subscription operations for Management Groups.
"""

helps['managementgroups group list'] = """
    type: command
    short-summary: List all management groups.
    long-summary: List of all management groups in the current tenant.
    examples:
        - name: List all management groups
          text: >
             az managementgroups group list
"""

helps['managementgroups group get'] = """
    type: command
    short-summary: Get a specific management group.
    long-summary: Get the details of the management group.
    parameters:
        - name: --group-name
          type: string
          short-summary: Name of the management group.
        - name: --expand -e
          type: bool
          short-summary: If given or true, lists the children in the first level of hierarchy.
        - name: --recurse -r
          type: bool
          short-summary: If given or true, lists the children in all levels of hierarchy.
    examples:
        - name: Get a management group.
          text: >
             az managementgroups group get --group-name <group_name>
        - name: Get a management group with children in the first level of hierarchy.
          text: >
             az managementgroups group get --group-name <group_name> -e
        - name: Get a management group with children in all levels of hierarchy.
          text: >
             az managementgroups group get --group-name <group_name> -e -r
"""

helps['managementgroups group new'] = """
    type: command
    short-summary: Add a new management group.
    long-summary: Add a new management group.
    parameters:
        - name: --group-name
          type: string
          short-summary: Name of the management group.
        - name: --display-name -d
          type: string
          short-summary: Sets the display name of the management group. If null, the group name is set as the display name.
        - name: --parent-id -p
          type: string
          short-summary: Sets the parent of the management group. A fully qualified id is required. If null, the root tenant group is set as the parent.
    examples:
        - name: Add a new management group.
          text: >
             az managementgroups group new --group-name <group_name>
        - name: Add a new management group with a specific display name.
          text: >
             az managementgroups group new --group-name <group_name> --display-name <display_name>
        - name: Add a new management group with a specific parent id.
          text: >
             az managementgroups group new --group-name <group_name> --parent-id <parent_id>
        - name: Add a new management group with a specific display name and parent id.
          text: >
             az managementgroups group new --group-name <group_name> --display-name <display_name> --parent-id <parent_id>
"""

helps['managementgroups group update'] = """
    type: command
    short-summary: Update an existing management group.
    long-summary: Update an existing management group.
    parameters:
        - name: --group-name
          type: string
          short-summary: Name of the management group.
        - name: --display-name -d
          type: string
          short-summary: Updates the display name of the management group. If null, no change is made.
        - name: --parent-id -p
          type: string
          short-summary: Update the parent of the management group. A fully qualified id is required. If null, no change is made.
    examples:
        - name: Update an existing management group with a specific display name.
          text: >
             az managementgroups group update --group-name <group_name> --display-name <display_name>
        - name: Update an existing management group with a specific parent id.
          text: >
             az managementgroups group update --group-name <group_name> --parent-id <parent_id>
        - name: Update an existing management group with a specific display name and parent id.
          text: >
             az managementgroups group update --group-name <group_name> --display-name <display_name> --parent-id <parent_id>
"""

helps['managementgroups group remove'] = """
    type: command
    short-summary: Remove an existing management group.
    long-summary: Remove an existing management group.
    parameters:
        - name: --group-name
          type: string
          short-summary: Name of the management group.
    examples:
        - name: Remove an existing management group
          text: >
             az managementgroups group remove --group-name <group_name>
"""

helps['managementgroups subscription new'] = """
    type: command
    short-summary: Add a subscription to a management group.
    long-summary: Add a subscription to a management group.
    parameters:
        - name: --group-name
          type: string
          short-summary: Name of the management group.
        - name: --subscription-id
          type: string
          short-summary: Subscription Id
    examples:
        - name: Add a subscription to a management group.
          text: >
             az managementgroups group new --group-name <group_name> --subscription-id <subscription_id>
"""

helps['managementgroups subscription remove'] = """
    type: command
    short-summary: Remove an existing subscription from a management group.
    long-summary: Remove an existing subscription from a management group.
    parameters:
        - name: --group-name
          type: string
          short-summary: Name of the management group.
        - name: --subscription-id
          type: string
          short-summary: Subscription Id
    examples:
        - name: Remove an existing subscription from a management group.
          text: >
             az managementgroups group remove --group-name <group_name> --subscription-id <subscription_id>
"""
