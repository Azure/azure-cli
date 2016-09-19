#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

from azure.cli.core.help_files import helps #pylint: disable=unused-import

#pylint: disable=line-too-long

helps['redis'] = """
    type: group
    short-summary: Access to a secure, dedicated cache for your Azure applications
"""

helps['redis patch-schedule'] = """
    type: group
    short-summary: Commands to manage redis patch schedules
"""