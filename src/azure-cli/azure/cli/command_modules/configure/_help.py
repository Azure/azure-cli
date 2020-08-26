# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps  # pylint: disable=unused-import
# pylint: disable=line-too-long, too-many-lines

helps['cache'] = """
type: group
short-summary: Commands to manage CLI objects cached using the `--defer` argument.
"""

helps['cache delete'] = """
type: command
short-summary: Delete an object from the cache.
"""

helps['cache list'] = """
type: command
short-summary: List the contents of the object cache.
"""

helps['cache purge'] = """
type: command
short-summary: Clear the entire CLI object cache.
"""

helps['cache show'] = """
type: command
short-summary: Show the contents of a specific object in the cache.
"""

helps['configure'] = """
type: command
short-summary: Manage Azure CLI configuration. This command is interactive.
parameters:
  - name: --defaults -d
    short-summary: >
        Space-separated 'name=value' pairs for common argument defaults.
examples:
  - name: Set default resource group, webapp and VM names.
    text: az configure --defaults group=myRG web=myweb vm=myvm
  - name: Clear default webapp and VM names.
    text: az configure --defaults vm='' web=''
"""

helps['local-context'] = """
type: group
short-summary: Manage Local Context
"""

helps['local-context on'] = """
type: command
short-summary: Turn on local context
"""

helps['local-context off'] = """
type: command
short-summary: Turn off local context
"""

helps['local-context show'] = """
type: command
short-summary: Show local context data
examples:
  - name: Show all local context value
    text: az local-context show
  - name: Show resource_group_name local context value
    text: az local-context show --name resource_group_name
"""

helps['local-context delete'] = """
type: command
short-summary: Delete local context data
examples:
  - name: Delete resource_group_name from local context
    text: az local-context delete --name resource_group_name
  - name: Clear all local context data
    text: az local-context delete --all
  - name: Delete local context persistence file
    text: az local-context delete --all --purge
  - name: Delete local context persistence file recursively
    text: az local-context delete --all --purge --recursive
"""
