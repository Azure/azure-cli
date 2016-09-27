#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

from azure.cli.core.help_files import helps #pylint: disable=unused-import

#pylint: disable=line-too-long

helps['appservice'] = """
    type: group
    short-summary: commands for managing your Azure web apps, app service plans, etc
"""

helps['appservice plan'] = """
    type: group
    short-summary: commands for managing your app service plans
"""

helps['appservice plan update'] = """
    type: command
    short-summary: update plan, including 'scale up' and 'scale out'
"""

helps['appservice plan create'] = """
    type: command
    short-summary: create a new plan
"""