# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import azure.cli.command_modules.lab._help  # pylint: disable=unused-import


def load_params(_):
    import azure.cli.command_modules.lab.params  # pylint: disable=redefined-outer-name, unused-variable


def load_commands():
    import azure.cli.command_modules.lab.commands  # pylint: disable=redefined-outer-name, unused-variable
