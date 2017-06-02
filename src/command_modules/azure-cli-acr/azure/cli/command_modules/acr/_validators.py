# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.util import CLIError
import azure.cli.core.azlogging as azlogging
from ._factory import get_acr_service_client


logger = azlogging.get_az_logger(__name__)


def validate_registry_name(namespace):
    if namespace.registry_name:
        client = get_acr_service_client().registries
        registry_name = namespace.registry_name

        result = client.check_name_availability(registry_name)

        if not result.name_available:  # pylint: disable=no-member
            raise CLIError(result.message)  # pylint: disable=no-member
