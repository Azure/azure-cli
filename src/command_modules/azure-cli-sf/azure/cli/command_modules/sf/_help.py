# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.core.help_files import helps


helps["sf"] = """
     type: group
     short-summary: Manage and administer an Azure Service Fabric cluster.
"""
helps["sf application"] = """
    type: group
    short-summary: Manage applications running on an Azure Service Fabric cluster.
"""
helps["sf chaos"] = """
    type: group
    short-summary: Manage an Azure Service Fabric Chaos service.
"""
helps["sf cluster"] = """
    type: group
    short-summary: Select and manage an Azure Service Fabric cluster.
"""
helps["sf compose"] = """
    type: group
    short-summary: Manage and deploy applications created from Docker Compose.
"""
helps["sf node"] = """
    type: group
    short-summary: Manage the nodes of an Azure Service Fabric cluster.
"""
helps["sf partition"] = """
    type: group
    short-summary: Manage the partitions of an Azure Service Fabric service.
"""
helps["sf replica"] = """
    type: group
    short-summary: Manage replicas of an Azure Service Fabric service partition.
"""
helps["sf service"] = """
    type: group
    short-summary: Manage services of an Azure Service Fabric application.
"""
