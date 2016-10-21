#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

from azure.cli.core.help_files import helps #pylint: disable=unused-import

#pylint: disable=line-too-long

helps['cloud'] = """
    type: group
    short-summary: Manage the Azure clouds registered
"""

helps['cloud list'] = """
            type: command
            short-summary: List the clouds registered
"""

helps['cloud show'] = """
            type: command
            short-summary: Show the endpoints and parameters for a cloud registered
"""

helps['cloud register'] = """
            type: command
            short-summary: Register a cloud
            long-summary: Register a cloud by passing in the configuration for it.
                        After a cloud is registered, it can be referenced in the context commands.
"""

helps['cloud unregister'] = """
            type: command
            short-summary: Unregister a cloud
"""
