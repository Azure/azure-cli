# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.help_files import helps


helps['lab'] = """
            type: group
            short-summary: Commands to manage Azure DevTest Lab.
            """
helps['lab vm'] = """
            type: group
            short-summary: Commands to manage vm of Azure DevTest Lab.
            """
helps['lab vm create'] = """
            type: command
            short-summary: Command to create vm of in Azure DevTest Lab.
            """
helps['lab custom-image'] = """
            type: group
            short-summary: Commands to manage custom images of Azure DevTest Lab.
            """
helps['lab gallery-image'] = """
            type: group
            short-summary: Commands to list gallery images of Azure DevTest Lab.
            """
helps['lab artifact'] = """
            type: group
            short-summary: Commands to manage artifact of Azure DevTest Lab.
            """
helps['lab vnet'] = """
            type: group
            short-summary: Commands to manage Azure DevTest Lab's Virtual Network.
            """
