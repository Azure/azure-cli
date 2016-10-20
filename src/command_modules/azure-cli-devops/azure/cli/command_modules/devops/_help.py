#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

from azure.cli.core.help_files import helps 

helps['devops'] = """
    type: group
    short-summary: Manages builds and releases for containerized micro-services.
"""

helps['devops release'] = """
    type: group
    short-summary: Commands to manage releases
"""

helps['devops build'] = """
    type: group
    short-summary: Commands to manage builds
"""