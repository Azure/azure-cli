# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.util import CLIError

MSG_TMPL = """
az component and subcommands are not available with the current Azure CLI installation.
If installed with apt-get, please use 'apt-get update' to update this installation.
If installed with Docker, please use 'docker pull' to update this installation.
If installed with Windows MSI, download the new MSI to update this installation.
{}
"""

def _raise_error(msg):
    raise CLIError(MSG_TMPL.format(msg))

def list_components():
    """ List the installed components """
    _raise_error("Use 'az --version' to list component versions.")

def list_available_components():
    """ List publicly available components that can be installed """
    _raise_error("No additional components available.")

def remove(component_name):
    """ Remove a component """
    _raise_error("Components cannot be removed.")

def update(private=False, pre=False, link=None, additional_components=None, allow_third_party=False):
    """ Update the CLI and all installed components """
    _raise_error("Components cannot be updated.")
