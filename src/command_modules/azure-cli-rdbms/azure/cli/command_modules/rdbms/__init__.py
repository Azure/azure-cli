# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import azure.cli.command_modules.rdbms.help  # pylint: disable=unused-import

__all__ = ['load_params', 'load_commands']


def load_params(_):
    import azure.cli.command_modules.rdbms.params  # pylint: disable=redefined-outer-name


def load_commands():
    import azure.cli.command_modules.rdbms.commands  # pylint: disable=redefined-outer-name
