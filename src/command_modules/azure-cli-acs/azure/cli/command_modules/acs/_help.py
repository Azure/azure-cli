# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.help_files import helps

helps['acs dcos'] = """
    type: group
    short-summary: Commands to manage a DCOS orchestrated Azure container service.
"""

helps['acs create'] = """
            type: command
            long-summary: See https://azure.microsoft.com/en-us/documentation/articles/container-service-intro/ for an intro to Container Service.
"""

helps['acs'] = """
    type: group
    short-summary: Commands to manage Azure container services
"""
helps['acs create'] = """
    type: command
    short-summary: Create a container service with your preferred orchestrator
"""
helps['acs delete'] = """
    type: command
    short-summary: delete a container service
"""
helps['acs list'] = """
    type: command
    short-summary: list container services
"""
helps['acs show'] = """
    type: command
    short-summary: show a container service
"""
helps['acs scale'] = """
    type: command
    short-summary: change private agent count of a container service.
"""

