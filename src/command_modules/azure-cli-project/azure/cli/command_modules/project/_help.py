# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.help_files import helps

helps['project'] = """
    type: group
    short-summary: "Do *magic* project stuff."
"""

helps['project run'] = """
    type: command
    short-summary: "Set up automated build and deployment for a service on a kubernetes cluster in the current workspace."
"""

helps['project delete'] = """
    type: command
    short-summary: "Deletes the Azure resource group containing project's artifacts and the projectResource.json file."
"""