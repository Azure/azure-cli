# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps

# pylint: disable=line-too-long

helps['loganalytics query'] = """
    type: command
    short-summary: Query a Log Analytics workspace.
    parameters:
        - workspace: --workspace -w
          type: string
          short-summary: GUID of the Log Analytics workspace.
        - kql: --kql -k
          type: string
          short-summary: Query to execute over the Log Analytics data.
    examples:
        - name:
"""
