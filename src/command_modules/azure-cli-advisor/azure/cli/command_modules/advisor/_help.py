# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.help_files import helps

helps['advisor'] = """
    type: group
    short-summary: (PREVIEW) Manage Azure Advisor.
"""

helps['advisor configuration get'] = """
    type: group
    short-summary: Get Azure Advisor configuration.
"""

helps['advisor configuration set'] = """
    type: group
    short-summary: Set Azure Advisor configuration.
"""

helps['advisor recommendation generate'] = """
    type: group
    short-summary: Generate Azure Advisor recommendations.
"""

helps['advisor recommendation list'] = """
    type: group
    short-summary: List Azure Advisor recommendations.
"""

helps['advisor recommendation disable'] = """
    type: group
    short-summary: Disable Azure Advisor recommendations.
"""

helps['advisor recommendation enable'] = """
    type: group
    short-summary: Enable Azure Advisor recommendations.
"""
