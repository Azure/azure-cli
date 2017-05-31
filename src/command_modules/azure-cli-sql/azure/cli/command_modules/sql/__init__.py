# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import azure.cli.command_modules.sql._help  # pylint: disable=unused-import

__all__ = ['load_params', 'load_commands']


def load_params(_):
    import azure.cli.command_modules.sql.params  # pylint: disable=redefined-outer-name, unused-variable


def load_commands():
    import azure.cli.command_modules.sql.commands  # pylint: disable=redefined-outer-name, unused-variable
