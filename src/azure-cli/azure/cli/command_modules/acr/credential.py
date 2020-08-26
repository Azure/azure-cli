# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError

from ._utils import get_registry_by_name


def acr_credential_show(cmd, client, registry_name, resource_group_name=None):
    registry, resource_group_name = get_registry_by_name(cmd.cli_ctx, registry_name, resource_group_name)

    if registry.admin_user_enabled:  # pylint: disable=no-member
        return client.list_credentials(resource_group_name, registry_name)

    raise admin_not_enabled_error(registry_name)


def acr_credential_renew(cmd, client, registry_name, password_name, resource_group_name=None):
    registry, resource_group_name = get_registry_by_name(cmd.cli_ctx, registry_name, resource_group_name)

    if registry.admin_user_enabled:  # pylint: disable=no-member
        return client.regenerate_credential(
            resource_group_name, registry_name, password_name)

    raise admin_not_enabled_error(registry_name)


def admin_not_enabled_error(registry_name):
    return CLIError("Run 'az acr update -n {} --admin-enabled true' to enable admin first.".format(registry_name))
