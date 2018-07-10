# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps

helps['extension'] = """
    type: group
    short-summary: Manage and update CLI extensions.
"""

helps['extension add'] = """
    type: command
    short-summary: Add an extension.
    examples:
    - name: Add extension by name
      text: az extension add --name anextension
    - name: Add extension from URL
      text: az extension add --source https://contoso.com/anextension-0.0.1-py2.py3-none-any.whl
    - name: Add extension from local disk
      text: az extension add --source ~/anextension-0.0.1-py2.py3-none-any.whl
    - name: Add extension from local disk and use pip proxy for dependencies
      text: az extension add --source ~/anextension-0.0.1-py2.py3-none-any.whl
            --pip-proxy https://user:pass@proxy.server:8080
"""

helps['extension list'] = """
    type: command
    short-summary: List the installed extensions.
"""

helps['extension list-available'] = """
    type: command
    short-summary: List publicly available extensions.
    examples:
    - name: List all publicly available extensions
      text: az extension list-available
    - name: List details on a particular extension
      text: az extension list-available --show-details --query anextension
"""

helps['extension show'] = """
    type: command
    short-summary: Show an extension.
"""

helps['extension remove'] = """
    type: command
    short-summary: Remove an extension.
"""

helps['extension update'] = """
    type: command
    short-summary: Update an extension.
    examples:
    - name: Update an extension by name
      text: az extension update --name anextension
    - name: Update an extension by name and use pip proxy for dependencies
      text: az extension update --name anextension --pip-proxy https://user:pass@proxy.server:8080
"""
