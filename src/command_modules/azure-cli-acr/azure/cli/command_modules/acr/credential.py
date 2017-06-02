# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.util import CLIError
import azure.cli.core.azlogging as azlogging

from ._factory import get_acr_service_client
from ._utils import get_registry_by_name


logger = azlogging.get_az_logger(__name__)


def acr_credential_show(registry_name, resource_group_name=None):
    """Gets the login credentials for the specified container registry.
    :param str registry_name: The name of container registry
    :param str resource_group_name: The name of resource group
    """
    registry, resource_group_name = get_registry_by_name(registry_name, resource_group_name)
    client = get_acr_service_client().registries

    if registry.admin_user_enabled:  # pylint: disable=no-member
        return client.list_credentials(resource_group_name, registry_name)

    admin_not_enabled_error(registry_name)


def acr_credential_renew(registry_name, password_name, resource_group_name=None):
    """Regenerates one of the login credentials for the specified container registry.
    :param str registry_name: The name of container registry
    :param str password_name: The name of password to regenerate
    :param str resource_group_name: The name of resource group
    """
    registry, resource_group_name = get_registry_by_name(registry_name, resource_group_name)
    client = get_acr_service_client().registries

    if registry.admin_user_enabled:  # pylint: disable=no-member
        return client.regenerate_credential(
            resource_group_name, registry_name, password_name)

    admin_not_enabled_error(registry_name)


def admin_not_enabled_error(registry_name):
    raise CLIError("Run 'az acr update -n {} --admin-enabled true' to enable admin first.".format(
        registry_name))
