# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core._util import CLIError

def _raise_error(msg):
    raise CLIError("This operation is not available in this packaged version of the CLI.\n{}".format(msg))

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
