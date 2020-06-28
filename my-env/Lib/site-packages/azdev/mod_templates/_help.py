# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps  # pylint: disable=unused-import


helps['{{ name }}'] = """
    type: group
    short-summary: Commands to manage {{ display_name_plural }}.
"""

helps['{{ name }} create'] = """
    type: command
    short-summary: Create a {{ display_name }}.
"""

helps['{{ name }} list'] = """
    type: command
    short-summary: List {{ display_name_plural }}.
"""
{% if sdk_path %}
helps['{{ name }} delete'] = """
    type: command
    short-summary: Delete a {{ display_name }}.
"""

helps['{{ name }} show'] = """
    type: command
    short-summary: Show details of a {{ display_name }}.
"""

helps['{{ name }} update'] = """
    type: command
    short-summary: Update a {{ display_name }}.
"""
{% else %}
# helps['{{ name }} delete'] = """
#     type: command
#     short-summary: Delete a {{ display_name }}.
# """

# helps['{{ name }} show'] = """
#     type: command
#     short-summary: Show details of a {{ display_name }}.
# """

# helps['{{ name }} update'] = """
#     type: command
#     short-summary: Update a {{ display_name }}.
# """
{% endif %}