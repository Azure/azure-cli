# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=unused-import
import azure.cli.command_modules.dla._help


def load_params(_):
    # pylint: disable=redefined-outer-name
    import azure.cli.command_modules.dla._params


def load_commands():
    # pylint: disable=redefined-outer-name
    import azure.cli.command_modules.dla.commands
