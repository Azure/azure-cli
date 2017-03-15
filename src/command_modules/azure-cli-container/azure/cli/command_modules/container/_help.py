# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.help_files import helps

helps['container'] = """
    type: group
    short-summary: "Set up automated builds and deployments for multi-container Docker applications."
    long-summary: These commands are in preview.
"""

helps['container release'] = """
    type: group
    short-summary: "Set up automated builds and deployments for a multi-container Docker application."
    long-summary: These commands are in preview.
"""

helps['container build'] = """
    type: group
    short-summary: "Set up automated builds for a multi-container Docker application."
    long-summary: These commands are in preview.
"""
