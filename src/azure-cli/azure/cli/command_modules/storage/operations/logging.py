# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def disable_logging(client, timeout=None):
    for s in client:
        s.disable_logging(timeout=timeout)


def set_logging(client, log, retention, timeout=None, version=None):
    for s in client:
        s.set_logging('r' in log, 'w' in log, 'd' in log, retention, timeout=timeout, version=version)


def get_logging(client, timeout=None):
    from azure.common import AzureException
    results = {}
    for s in client:
        try:
            results[s.name] = s.get_logging(timeout)
        except (KeyError, AzureException):
            import sys
            from azure.cli.core.azlogging import CommandLoggerContext
            from knack.log import get_logger

            logger = get_logger(__name__)
            with CommandLoggerContext(logger):
                logger.error("Your storage account doesn't support logging for %s service. Please change value for "
                             "--services in your commands.", s.name)
                sys.exit(1)
    return results
