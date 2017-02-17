# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.help_files import helps

helps['acs'] = """
     type: group
     short-summary: Commands to manage Azure Container Services
 """
helps['acs dcos'] = """
    type: group
    short-summary: Commands to manage a DCOS orchestrated Azure Container Service.
"""
helps['acs kubernetes'] = """
    type: group
    short-summary: Commands to manage a Kubernetes orchestrated Azure Container Service.
"""
helps['acs scale'] = """
    type: command
    short-summary: Change private agent count of a container service.
"""
helps['acs install-cli'] = """
    type: command
    short-summary: Downloads the DCOS/Kubernetes command line.
"""
