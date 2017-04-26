# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.help_files import helps

helps['acs'] = """
     type: group
     short-summary: Manage Azure container services.
"""
helps['acs dcos'] = """
    type: group
    short-summary: Manage a DCOS orchestrated Azure container service.
"""
helps['acs kubernetes'] = """
    type: group
    short-summary: Manage a Kubernetes orchestrated Azure Container service.
"""
helps['acs kubernetes get-credentials'] = """
    type: command
    short-summary: Download and install credentials to access your cluster.
"""
helps['acs scale'] = """
    type: command
    short-summary: Change the private agent count of a container service.
"""
helps['acs install-cli'] = """
    type: command
    short-summary: Download the DCOS/Kubernetes command line.
"""
