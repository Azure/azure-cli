# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os

from knack.log import get_logger
from knack.util import CLIError

from .util import should_disable_connection_verify, DISABLE_VERIFY_VARIABLE_NAME

logger = get_logger(__name__)

REQUESTS_CA_BUNDLE = "REQUESTS_CA_BUNDLE"


def change_ssl_cert_verification(client):
    if should_disable_connection_verify():
        logger.warning("Connection verification disabled by environment variable %s",
                       DISABLE_VERIFY_VARIABLE_NAME)
        client.config.connection.verify = False
    elif REQUESTS_CA_BUNDLE in os.environ:
        ca_bundle_file = os.environ[REQUESTS_CA_BUNDLE]
        if not os.path.isfile(ca_bundle_file):
            raise CLIError('REQUESTS_CA_BUNDLE environment variable is specified with an invalid file path')
        logger.debug("Using CA bundle file at '%s'.", ca_bundle_file)
        client.config.connection.verify = ca_bundle_file
    return client


def change_ssl_cert_verification_track2():
    client_kwargs = {}
    if should_disable_connection_verify():
        logger.warning("Connection verification disabled by environment variable %s",
                       DISABLE_VERIFY_VARIABLE_NAME)
        client_kwargs['connection_verify'] = False
    elif REQUESTS_CA_BUNDLE in os.environ:
        ca_bundle_file = os.environ[REQUESTS_CA_BUNDLE]
        if not os.path.isfile(ca_bundle_file):
            raise CLIError('REQUESTS_CA_BUNDLE environment variable is specified with an invalid file path')
        logger.debug("Using CA bundle file at '%s'.", ca_bundle_file)
        client_kwargs['connection_verify'] = ca_bundle_file
    return client_kwargs
