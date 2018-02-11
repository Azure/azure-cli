# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps

helps['managementpartner'] = """
    type: group
    short-summary: Manage Azure ManagementPartner.
"""

helps['managementpartner create'] = """
    type: command
    short-summary: Create new management partner
    long-summary: Add a management partner id to the current user
    parameters:
        - name: --partner-id
          type: string
          short-summary: Id of management partner
"""

helps['managementpartner get'] = """
    type: command
    short-summary: Get the management partner
    long-summary: Get the management partner id for the current user
    parameters:
        - name: --partner-id
          type: string
          short-summary: Id of management partner
"""

helps['managementpartner update'] = """
    type: command
    short-summary: Update the management partner
    long-summary: update the management partner id for the current user
    parameters:
        - name: --partner-id
          type: string
          short-summary: Id of management partner
"""

helps['managementpartner remove'] = """
    type: command
    short-summary: Remove the management partner
    long-summary: Remove the management partner id for the current user
    parameters:
        - name: --partner-id
          type: string
          short-summary: Id of management partner
"""
