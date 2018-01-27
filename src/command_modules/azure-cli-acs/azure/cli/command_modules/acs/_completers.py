# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands.parameters import get_one_of_subscription_locations
from azure.cli.core.decorators import Completer


@Completer
def get_k8s_upgrades_completion_list(cmd, prefix, namespace, **kwargs):  # pylint: disable=unused-argument
    """Return Kubernetes versions available for upgrading an existing cluster."""
    location = _get_location(cmd, namespace)
    return get_k8s_upgrades(cmd.cli_ctx, location, None, None)


def get_k8s_upgrades(cli_ctx, location, resource_group, name):
    return ['get_k8s_upgrades', 'NOT', 'IMPLEMENTED']


@Completer
def get_k8s_versions_completion_list(cmd, prefix, namespace, **kwargs):  # pylint: disable=unused-argument
    """Return Kubernetes versions available for provisioning a new cluster."""
    location = _get_location(cmd, namespace)
    return get_k8s_versions(cmd.cli_ctx, location)


def get_k8s_versions(cli_ctx, location):
    """Return a list of Kubernetes versions available for a new cluster."""
    from ._client_factory import cf_container_services
    from jmespath import search
    results = cf_container_services(cli_ctx).list_orchestrators(location, resource_type='managedClusters').as_dict()
    # Flatten all the "orchestrator_version" fields into one set
    jmespath_query = 'orchestrators[*].[orchestrator_version, upgrades[*].orchestrator_version[]][][]'
    return set(search(jmespath_query, results))


@Completer
def get_vm_size_completion_list(cmd, prefix, namespace, **kwargs):  # pylint: disable=unused-argument
    """Return the intersection of the VM sizes allowed by the ACS SDK with those returned by the Compute Service."""
    from azure.mgmt.containerservice.models import ContainerServiceVMSizeTypes
    location = _get_location(cmd, namespace)
    result = get_vm_sizes(cmd.cli_ctx, location)
    return sorted(set(r.name for r in result) & set(c.value for c in ContainerServiceVMSizeTypes))


def get_vm_sizes(cli_ctx, location):
    from ._client_factory import cf_compute_service
    return list(cf_compute_service(cli_ctx).virtual_machine_sizes.list(location))


def _get_location(cmd, namespace):
    location = namespace.location
    if not location:
        # # TODO: look up location from rg
        # location = namespace.resource_group_name
        if not location:
            location = get_one_of_subscription_locations(cmd.cli_ctx)
    return location
