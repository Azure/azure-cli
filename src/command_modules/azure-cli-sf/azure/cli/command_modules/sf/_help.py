# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.core.help_files import helps


helps["sf"] = """
     type: group
     short-summary: Manage and administer a Service Fabric cluster
"""
helps["sf application"] = """
    type: group
    short-summary: Manage the applications running on a Service Fabric cluster
"""
helps["sf chaos"] = """
    type: group
    short-summary: Manage the Service Fabric Chaos service, designed to
                   simulate real failures
"""
helps["sf cluster"] = """
    type: group
    short-summary: Select and manage a Service Fabric cluster
"""
helps["sf compose"] = """
    type: group
    short-summary: Manage and deploy applications created from Docker Compose
"""
helps["sf node"] = """
    type: group
    short-summary: Manage the nodes that create a Service Fabric cluster
"""
helps["sf partition"] = """
    type: group
    short-summary: Manage the partitions of a Service Fabric service
"""
helps["sf replica"] = """
    type: group
    short-summary: Manage the replicas of a Service Fabric service partition
"""
helps["sf service"] = """
    type: group
    short-summary: Manage the services of a Service Fabric application
"""
