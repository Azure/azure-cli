# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from knack.help_files import helps

helps['managementpartner'] = """
    type: group
    short-summary: Allows the partners to associate a Microsoft Partner Network(MPN) ID to a user or service principal in the customer's Azure directory.
"""

helps['managementpartner create'] = """
    type: command
    short-summary: Associates a Microsoft Partner Network(MPN) ID to the current authenticated user or service principal.
"""

helps['managementpartner show'] = """
    type: command
    short-summary: Gets the Microsoft Partner Network(MPN) ID of the current authenticated user or service principal.
"""

helps['managementpartner update'] = """
    type: command
    short-summary: Updates the Microsoft Partner Network(MPN) ID of the current authenticated user or service principal.
"""

helps['managementpartner delete'] = """
    type: command
    short-summary: Delete the Microsoft Partner Network(MPN) ID of the current authenticated user or service principal.
"""
