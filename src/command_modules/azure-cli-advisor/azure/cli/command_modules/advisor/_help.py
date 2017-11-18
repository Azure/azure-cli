# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.help_files import helps

helps['advisor'] = """
    type: group
    short-summary: (PREVIEW) Manage Azure Advisor.
"""

helps['advisor configuration'] = """
    type: group
    short-summary: Manage Azure Advisor configuration.
"""

helps['advisor recommendation'] = """
    type: group
    short-summary: Review Azure Advisor recommendations.
"""

helps['advisor configuration get'] = """
    type: command
    short-summary: Get Azure Advisor configuration.
"""

helps['advisor configuration set'] = """
    type: command
    short-summary: Set Azure Advisor configuration.
"""

helps['advisor recommendation generate'] = """
    type: command
    short-summary: Generate Azure Advisor recommendations.
"""

helps['advisor recommendation list'] = """
    type: command
    short-summary: List Azure Advisor recommendations.
"""

helps['advisor recommendation disable'] = """
    type: command
    short-summary: Disable Azure Advisor recommendations.
"""

helps['advisor recommendation enable'] = """
    type: command
    short-summary: Enable Azure Advisor recommendations.
"""
