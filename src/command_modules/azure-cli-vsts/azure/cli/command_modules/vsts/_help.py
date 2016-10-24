#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

from azure.cli.core.help_files import helps

helps['vsts'] = """
    type: group
    short-summary: "Set up automated builds and deployments for multi-container
        Docker applications."
"""

helps['vsts release'] = """
    type: group
    short-summary: "Set up automated builds and deployments for a
        multi-container Docker application."
"""

helps['vsts build'] = """
    type: group
    short-summary: "Set up automated builds for a multi-container Docker application."
"""