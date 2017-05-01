# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.help_files import helps  # pylint: disable=unused-import


helps['documentdb'] = """
    type: group
    short-summary: Manage Azure DocumentDB (NoSQL) database accounts.
"""

helps['documentdb database'] = """
    type: group
    short-summary: Manage Azure DocumentDB databases.
"""

helps['documentdb collection'] = """
    type: group
    short-summary: Manage Azure DocumentDB collections.
"""
