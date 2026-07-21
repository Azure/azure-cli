# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps  # pylint: disable=unused-import
# pylint: disable=line-too-long, too-many-lines

helps['config'] = """
type: group
short-summary: Manage Azure CLI configuration.
long-summary: Available since Azure CLI 2.10.0.
"""

helps['config set'] = """
type: command
short-summary: Set a configuration.
long-summary: |
    For available configuration options, see https://learn.microsoft.com/cli/azure/azure-cli-configuration.
    By default without specifying --local, the configuration will be saved to `~/.azure/config`.
examples:
  - name: Disable color with `core.no_color`.
    text: az config set core.no_color=true
  - name: Hide warnings and only show errors with `core.only_show_errors`.
    text: az config set core.only_show_errors=true
  - name: Turn on client-side telemetry.
    text: az config set core.collect_telemetry=true
  - name: Turn on file logging and set its location.
    text: |-
        az config set logging.enable_log_file=true
        az config set logging.log_dir=~/az-logs
  - name: Set the default location to `westus2` and default resource group to `myRG`.
    text: az config set defaults.location=westus2 defaults.group=MyResourceGroup
  - name: Set the default resource group to `myRG` on a local scope.
    text: az config set defaults.group=myRG --local
"""

helps['config get'] = """
type: command
short-summary: Get a configuration.
examples:
  - name: Get all configurations.
    text: az config get
  - name: Get configurations in `core` section.
    text: az config get core
  - name: Get the configuration of key `core.no_color`.
    text: az config get core.no_color
"""

helps['config unset'] = """
type: command
short-summary: Unset a configuration.
examples:
  - name: Unset the configuration of key `core.no_color`.
    text: az config unset core.no_color
"""

helps['config param-persist'] = """
type: group
short-summary: Manage parameter persistence.
"""

helps['config param-persist on'] = """
type: command
short-summary: Turn on parameter persistence.
"""

helps['config param-persist off'] = """
type: command
short-summary: Turn off parameter persistence.
"""

helps['config param-persist show'] = """
type: command
short-summary: Show parameter persistence data.
examples:
  - name: Show all parameter persistence value
    text: az config param-persist show
  - name: Show resource_group_name parameter persistence value
    text: az config param-persist show resource_group_name
"""

helps['config param-persist delete'] = """
type: command
short-summary: Delete parameter persistence data.
examples:
  - name: Delete resource_group_name from parameter persistence
    text: az config param-persist delete resource_group_name
  - name: Clear all parameter persistence data
    text: az config param-persist delete --all
  - name: Delete parameter persistence file
    text: az config param-persist delete --all --purge
  - name: Delete parameter persistence file recursively
    text: az config param-persist delete --all --purge --recursive
"""
