# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import azure.cli.command_modules.batch._help  # pylint: disable=unused-import
import azure.cli.core.azlogging as azlogging


logger = azlogging.get_az_logger(__name__)


def load_params(_):
    import azure.cli.command_modules.batch._params  # pylint: disable=redefined-outer-name, unused-variable
    try:
        import azure.cli.command_modules.batch_extensions._params
    except ImportError as exp:
        # Optional Batch Extensions not installed
        logger.debug("Did not load Batch Extensions module")
        logger.debug(str(exp))


def load_commands():
    import azure.cli.command_modules.batch.commands  # pylint: disable=redefined-outer-name, unused-variable
    try:
        import azure.cli.command_modules.batch_extensions.commands
    except ImportError as exp:
        # Optional Batch Extensions not installed
        logger.debug("Did not load Batch Extensions module")
        logger.debug(str(exp))
