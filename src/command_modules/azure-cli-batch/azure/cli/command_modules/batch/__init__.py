# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import azure.cli.command_modules.batch._help  # pylint: disable=unused-import

from knack.log import get_logger

logger = get_logger(__name__)


def load_params(_):
    import azure.cli.command_modules.batch._params  # pylint: disable=redefined-outer-name, unused-variable


def load_commands():
    import azure.cli.command_modules.batch.commands  # pylint: disable=redefined-outer-name, unused-variable
