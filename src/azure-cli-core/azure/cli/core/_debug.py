#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

import os
import azure.cli.core._logging as _logging

logger = _logging.get_az_logger(__name__)

DISABLE_VERIFY_VARIABLE_NAME = "AZURE_CLI_DISABLE_CONNECTION_VERIFICATION"

def allow_debug_connection(client):
    if should_disable_connection_verify():
        logger.warning("Connection verification disabled by environment variable %s",
                       DISABLE_VERIFY_VARIABLE_NAME)
        client.config.connection.verify = False

def should_disable_connection_verify():
    return bool(os.environ.get(DISABLE_VERIFY_VARIABLE_NAME))

