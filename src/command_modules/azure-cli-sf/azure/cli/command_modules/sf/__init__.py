# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import azure.cli.command_modules.sf._help  # pylint: disable=unused-import


def load_params(_):
    # pylint: disable=redefined-outer-name
    import azure.cli.command_modules.sf._params


def load_commands():
    # pylint: disable=redefined-outer-name
    import azure.cli.command_modules.sf.commands
