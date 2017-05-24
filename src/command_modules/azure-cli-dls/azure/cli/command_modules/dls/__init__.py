# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=unused-import
import azure.cli.command_modules.dls._help


def load_params(_):
    import azure.cli.command_modules.dls._params  # pylint: disable=redefined-outer-name, unused-variable


def load_commands():
    import azure.cli.command_modules.dls.commands  # pylint: disable=redefined-outer-name, unused-variable
