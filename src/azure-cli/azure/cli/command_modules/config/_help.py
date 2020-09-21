# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps  # pylint: disable=unused-import
# pylint: disable=line-too-long, too-many-lines

helps['config'] = """
type: group
short-summary: Manage Azure CLI configuration.
"""

helps['config set'] = """
type: command
short-summary: Set a configuration.
long-summary: |
    For available configuration options, see https://docs.microsoft.com/en-us/cli/azure/azure-cli-configuration.
    By default without specifying --local, the configuration will be saved to `~/.azure/config`.
examples:
  - name: Disable color.
    text: az config set no_color=true
  - name: Hide warnings and only show errors.
    text: az config set only_show_errors=true
  - name: Set the default location to `westus2` and default resource group to `myRG`.
    text: az config set defaults.location=westus2 defaults.group=MyResourceGroup
  - name: Set the default resource group to `myRG` on a local scope.
    text: az config set defaults.group=myRG --local
  - name: Turn on client-side telemetry.
    text: az config set collect_telemetry=true
  - name: Turn on file logging and set its location.
    text: az config set logging.enable_log_file=true logging.log_dir=~/az-logs
"""

helps['config get'] = """
type: command
short-summary: Get a configuration.
examples:
  - name: Get all configured options.
    text: az config get
  - name: Get the configured value of option `no_color`.
    text: az config get no_color
  - name: Get options in the `core` section. Note that `core` is followed by a dot (.).
    text: az config get core.
  - name: Get configured defaults. Note that `defaults` is followed by a dot (.).
    text: az config get defaults.
  - name: Get the configured default resource group.
    text: az config get defaults.group
"""

helps['config unset'] = """
type: command
short-summary: Unset a configuration.
examples:
  - name: Unset `no_color`.
    text: az config unset no_color
  - name: Unset the configured default resource group.
    text: az config unset defaults.group
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
