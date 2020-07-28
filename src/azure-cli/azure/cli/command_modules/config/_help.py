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
