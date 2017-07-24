# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# Each package management system should patch this file with their own implementations of these.
from knack.log import get_logger

CLI_PACKAGE_NAME = 'azure-cli'
COMPONENT_PREFIX = 'azure-cli-'

logger = get_logger(__name__)


def handle_module_not_installed(module_name):
    try:
        import xmlrpclib
    except ImportError:
        import xmlrpc.client as xmlrpclib  # pylint: disable=import-error
    query = {'author': 'Microsoft Corporation', 'author_email': 'azpycli'}
    logger.debug("Checking PyPI for modules using query '%s'", query)
    client = xmlrpclib.ServerProxy('https://pypi.python.org/pypi')
    pypi_hits = client.search(query)
    logger.debug("Found %d result(s)", len(pypi_hits))
    for hit in pypi_hits:
        if hit['name'] == '{}{}'.format(COMPONENT_PREFIX, module_name):
            logger.debug("Found module that matches '%s' - %s", module_name, hit)
            logger.warning("Install the '%s' module with 'az component update --add %s'",
                           module_name, module_name)
