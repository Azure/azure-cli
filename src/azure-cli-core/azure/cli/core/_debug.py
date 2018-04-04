# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os

from knack.log import get_logger
from .util import should_disable_connection_verify, DISABLE_VERIFY_VARIABLE_NAME
logger = get_logger(__name__)

ADAL_PYTHON_SSL_NO_VERIFY = "ADAL_PYTHON_SSL_NO_VERIFY"


def change_ssl_cert_verification(client):
    if should_disable_connection_verify():
        logger.warning("Connection verification disabled by environment variable %s",
                       DISABLE_VERIFY_VARIABLE_NAME)
        os.environ[ADAL_PYTHON_SSL_NO_VERIFY] = '1'
        client.config.connection.verify = False
    return client


def allow_debug_adal_connection():
    if should_disable_connection_verify():
        os.environ[ADAL_PYTHON_SSL_NO_VERIFY] = '1'
