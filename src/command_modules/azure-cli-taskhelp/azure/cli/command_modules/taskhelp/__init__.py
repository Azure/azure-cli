# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


import azure.cli.command_modules.taskhelp._help  # pylint: disable=unused-import


def load_params(_):
    pass


def load_commands():
    import azure.cli.command_modules.taskhelp.commands  # pylint: disable=redefined-outer-name
