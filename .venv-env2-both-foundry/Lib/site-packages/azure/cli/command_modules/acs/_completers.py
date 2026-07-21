# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands.parameters import get_one_of_subscription_locations
from azure.cli.core.decorators import Completer


@Completer
def get_k8s_upgrades_completion_list(cmd, prefix, namespace, **kwargs):  # pylint: disable=unused-argument
    """Return Kubernetes versions available for upgrading an existing cluster."""
    resource_group = getattr(namespace, 'resource_group_name', None)
    name = getattr(namespace, 'name', None)
    return get_k8s_upgrades(cmd.cli_ctx, resource_group, name) if resource_group and name else None


def get_k8s_upgrades(cli_ctx, resource_group, name):
    from azure.cli.command_modules.acs._client_factory import cf_managed_clusters

    results = cf_managed_clusters(cli_ctx).get_upgrade_profile(resource_group, name).as_dict()
    return results['control_plane_profile']['upgrades']


@Completer
def get_k8s_versions_completion_list(cmd, prefix, namespace, **kwargs):  # pylint: disable=unused-argument
    """Return Kubernetes versions available for provisioning a new cluster."""
    location = _get_location(cmd.cli_ctx, namespace)
    return get_k8s_versions(cmd.cli_ctx, location) if location else None


def get_k8s_versions(cli_ctx, location):
    """Return a list of Kubernetes versions available for a new cluster."""
    from azure.cli.command_modules.acs._client_factory import cf_managed_clusters
    from jmespath import search

    results = cf_managed_clusters(cli_ctx).list_kubernetes_versions(location).as_dict()
    # Flatten all the "orchestrator_version" fields into one array
    return search("values[*].patchVersions.keys(@)[]", results)


def get_vm_sizes(cli_ctx, location):
    from azure.cli.command_modules.acs._client_factory import get_compute_client

    return get_compute_client(cli_ctx).virtual_machine_sizes.list(location)


def _get_location(cli_ctx, namespace):
    """
    Return an Azure location by using an explicit `--location` argument, then by `--resource-group`, and
    finally by the subscription if neither argument was provided.
    """
    location = None
    if getattr(namespace, 'location', None):
        location = namespace.location
    elif getattr(namespace, 'resource_group_name', None):
        location = _get_location_from_resource_group(cli_ctx, namespace.resource_group_name)
    if not location:
        location = get_one_of_subscription_locations(cli_ctx)
    return location


def _get_location_from_resource_group(cli_ctx, resource_group_name):
    from azure.cli.command_modules.acs._client_factory import get_resource_groups_client
    from azure.core.exceptions import HttpResponseError

    try:
        rg = get_resource_groups_client(cli_ctx).get(resource_group_name)
        return rg.location
    except HttpResponseError as err:
        # Print a warning if the user hit [TAB] but the `--resource-group` argument was incorrect.
        # For example: "Warning: Resource group 'bogus' could not be found."
        from argcomplete import warn
        warn('Warning: {}'.format(err.message))
