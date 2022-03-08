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
    from ._client_factory import cf_managed_clusters

    results = cf_managed_clusters(cli_ctx).get_upgrade_profile(resource_group, name).as_dict()
    return results['control_plane_profile']['upgrades']


@Completer
def get_k8s_versions_completion_list(cmd, prefix, namespace, **kwargs):  # pylint: disable=unused-argument
    """Return Kubernetes versions available for provisioning a new cluster."""
    location = _get_location(cmd.cli_ctx, namespace)
    return get_k8s_versions(cmd.cli_ctx, location) if location else None


def get_k8s_versions(cli_ctx, location):
    """Return a list of Kubernetes versions available for a new cluster."""
    from ._client_factory import cf_container_services
    from jmespath import search

    results = cf_container_services(cli_ctx).list_orchestrators(location, resource_type='managedClusters').as_dict()
    # Flatten all the "orchestrator_version" fields into one array
    return search('orchestrators[*].orchestrator_version', results)


@Completer
def get_vm_size_completion_list(cmd, prefix, namespace, **kwargs):  # pylint: disable=unused-argument
    """Return the intersection of the VM sizes allowed by the ACS SDK with those returned by the Compute Service."""
    from azure.mgmt.containerservice.models import ContainerServiceVMSizeTypes

    location = _get_location(cmd.cli_ctx, namespace)
    result = get_vm_sizes(cmd.cli_ctx, location)
    return set(r.name for r in result) & set(c.value for c in ContainerServiceVMSizeTypes)


def get_vm_sizes(cli_ctx, location):
    from ._client_factory import cf_compute_service

    return cf_compute_service(cli_ctx).virtual_machine_sizes.list(location)


@Completer
def get_ossku_completion_list(cmd, prefix, namespace, **kwargs):  # pylint: disable=unused-argument
    """Return the list of allowed os-sku values"""

    return ["Ubuntu", "CBLMariner"]


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
    from ._client_factory import cf_resource_groups
    from msrestazure.azure_exceptions import CloudError

    try:
        rg = cf_resource_groups(cli_ctx).get(resource_group_name)
        return rg.location
    except CloudError as err:
        # Print a warning if the user hit [TAB] but the `--resource-group` argument was incorrect.
        # For example: "Warning: Resource group 'bogus' could not be found."
        from argcomplete import warn
        warn('Warning: {}'.format(err.message))
