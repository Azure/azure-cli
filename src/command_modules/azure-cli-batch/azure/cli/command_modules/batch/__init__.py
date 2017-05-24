# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import azure.cli.command_modules.batch._help  # pylint: disable=unused-import


def load_params(_):
    import azure.cli.command_modules.batch._params  # pylint: disable=redefined-outer-name, unused-variable
    try:
        import azure.cli.command_modules.batch_extensions._params
    except ImportError:
        pass  # Optional Batch Extensions not installed


def load_commands():
    import azure.cli.command_modules.batch.commands  # pylint: disable=redefined-outer-name, unused-variable
    try:
        import azure.cli.command_modules.batch_extensions.commands
    except ImportError:
        pass  # Optional Batch Extensions not installed
