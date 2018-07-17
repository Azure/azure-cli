# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps

# pylint: disable=line-too-long

helps['search'] = """
    type: group
    short-summary: Manage Azure Search services, admin keys and query keys.
"""

helps['search services'] = """
    type: group
    short-summary: Manage Azure Search services.
"""

helps['search adminkeys'] = """
    type: group
    short-summary: Manage Azure Search admin keys.
"""

helps['search querykeys'] = """
    type: group
    short-summary: Manage Azure Search query keys.
"""
