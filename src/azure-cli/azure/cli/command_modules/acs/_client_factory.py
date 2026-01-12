# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.core.commands.parameters import get_resources_in_subscription
from azure.cli.core.profiles import ResourceType
from azure.mgmt.msi import ManagedServiceIdentityClient
from knack.util import CLIError

# Note: cf_xxx, as the client_factory option value of a command group at command declaration, it should ignore
# parameters other than cli_ctx; get_xxx_client is used as the client of other services in the command implementation,
# and usually accepts subscription_id as a parameter to reconfigure the subscription when sending the request


# container service clients
def get_container_service_client(cli_ctx, subscription_id=None):
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_CONTAINERSERVICE, subscription_id=subscription_id)


def cf_container_services(cli_ctx, *_):
    return get_container_service_client(cli_ctx).container_services


def cf_managed_clusters(cli_ctx, *_):
    return get_container_service_client(cli_ctx).managed_clusters


def cf_machines(cli_ctx, *_):
    return get_container_service_client(cli_ctx).machines


def cf_maintenance_configurations(cli_ctx, *_):
    return get_container_service_client(cli_ctx).maintenance_configurations


def cf_managed_namespaces(cli_ctx, *_):
    return get_container_service_client(cli_ctx).managed_namespaces


def cf_agent_pools(cli_ctx, *_):
    return get_container_service_client(cli_ctx).agent_pools


def cf_snapshots(cli_ctx, *_):
    return get_container_service_client(cli_ctx).snapshots


def get_snapshots_client(cli_ctx, subscription_id=None):
    return get_container_service_client(cli_ctx, subscription_id=subscription_id).snapshots


def cf_trustedaccess_role(cli_ctx, *_):
    return get_container_service_client(cli_ctx).trusted_access_roles


def cf_trustedaccess_role_binding(cli_ctx, *_):
    return get_container_service_client(cli_ctx).trusted_access_role_bindings


# dependent clients
def get_compute_client(cli_ctx, *_):
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_COMPUTE)


def get_resource_groups_client(cli_ctx, subscription_id=None):
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES,
                                   subscription_id=subscription_id).resource_groups


def get_resources_client(cli_ctx, subscription_id=None):
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES,
                                   subscription_id=subscription_id).resources


def get_container_registry_client(cli_ctx, subscription_id=None):
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_CONTAINERREGISTRY,
                                   subscription_id=subscription_id)


def get_auth_management_client(cli_ctx, scope=None, **_):
    import re

    subscription_id = None
    if scope:
        matched = re.match('/subscriptions/(?P<subscription>[^/]*)/', scope)
        if matched:
            subscription_id = matched.groupdict()['subscription']
        else:
            raise CLIError("{} does not contain subscription Id.".format(scope))
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_AUTHORIZATION, subscription_id=subscription_id)


def get_graph_client(cli_ctx):
    from azure.cli.command_modules.role import graph_client_factory
    return graph_client_factory(cli_ctx)


def get_resource_by_name(cli_ctx, resource_name, resource_type):
    """Returns the ARM resource in the current subscription with resource_name.
    :param str resource_name: The name of resource
    :param str resource_type: The type of resource
    """
    result = get_resources_in_subscription(cli_ctx, resource_type)
    elements = [item for item in result if item.name.lower() ==
                resource_name.lower()]

    if not elements:
        from azure.cli.core._profile import Profile
        profile = Profile(cli_ctx=cli_ctx)
        message = "The resource with name '{}' and type '{}' could not be found".format(
            resource_name, resource_type)
        try:
            subscription = profile.get_subscription(
                cli_ctx.data['subscription_id'])
            raise CLIError(
                "{} in subscription '{} ({})'.".format(message, subscription['name'], subscription['id']))
        except (KeyError, TypeError):
            raise CLIError(
                "{} in the current subscription.".format(message))

    elif len(elements) == 1:
        return elements[0]
    else:
        raise CLIError(
            "More than one resources with type '{}' are found with name '{}'.".format(
                resource_type, resource_name))


def get_msi_client(cli_ctx, subscription_id=None):
    return get_mgmt_service_client(cli_ctx, ManagedServiceIdentityClient,
                                   subscription_id=subscription_id)


def get_keyvault_client(cli_ctx, subscription_id=None):
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_KEYVAULT, subscription_id=subscription_id).vaults
