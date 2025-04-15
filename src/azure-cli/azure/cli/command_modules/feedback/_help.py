# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps  # pylint: disable=unused-import
# pylint: disable=line-too-long, too-many-lines

helps['feedback'] = """
type: command
short-summary: Send feedback to the Azure CLI Team.
long-summary: >-
    This command is interactive. If possible, it launches the default
    web browser to open GitHub issue creation page with the body auto-generated and pre-filled.
    You will have a chance to edit the issue body before submitting it.
"""

helps['survey'] = """
type: command
short-summary: Take Azure CLI survey.
long-summary: >-
    Help us improve Azure CLI by sharing your experience. This survey should take about 3 minutes.
    Learn more at https://go.microsoft.com/fwlink/?linkid=2203309.
"""
