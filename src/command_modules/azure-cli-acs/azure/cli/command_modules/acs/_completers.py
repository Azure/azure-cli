# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from distutils.version import StrictVersion

from azure.cli.core.commands.parameters import get_one_of_subscription_locations
from azure.cli.core.decorators import Completer
from azure.mgmt.containerservice.models import ContainerServiceVMSizeTypes

from ._client_factory import cf_compute_service, cf_container_services


@Completer
def get_vm_size_completion_list(cmd, prefix, namespace, **kwargs):  # pylint: disable=unused-argument
    """Return the intersection of the VM sizes allowed by the ACS SDK with those returned by the Compute Service."""
    try:
        location = namespace.location
    except AttributeError:
        # TODO: try the resource group's default location before falling back to this
        location = get_one_of_subscription_locations(cmd.cli_ctx)
    result = get_vm_sizes(cmd.cli_ctx, location)
    return sorted(set(r.name for r in result) & set(c.value for c in ContainerServiceVMSizeTypes))


def get_vm_sizes(cli_ctx, location):
    return list(cf_compute_service(cli_ctx).virtual_machine_sizes.list(location))


@Completer
def get_k8s_versions_completion_list(cmd, prefix, namespace, **kwargs):  # pylint: disable=unused-argument
    """Return Kubernetes versions available for provisioning a new cluster."""
    try:
        location = namespace.location
    except AttributeError:
        # TODO: try the resource group's default location before falling back to this
        location = get_one_of_subscription_locations(cmd.cli_ctx)
    return get_k8s_versions(cmd.cli_ctx, location)


def get_k8s_versions(cli_ctx, location):
    import jmespath
    results = cf_container_services(cli_ctx).list_orchestrators(location, resource_type='managedClusters').as_dict()
    r = jmespath.search('orchestrators[*].[orchestrator_version, upgrades[*].orchestrator_version[]][][]', results)
    return sorted(set(r), key=StrictVersion)


@Completer
def get_k8s_upgrades_completion_list(cmd, prefix, namespace, **kwargs):  # pylint: disable=unused-argument
    """Return Kubernetes versions available for upgrading an existing cluster."""
    try:
        location = namespace.location
    except AttributeError:
        # TODO: try the resource group's default location before falling back to this
        location = get_one_of_subscription_locations(cmd.cli_ctx)
    return get_k8s_upgrades(cmd.cli_ctx, location, None, None)


def get_k8s_upgrades(cli_ctx, location, resource_group, name):
    return ['get_k8s_upgrades', 'NOT', 'IMPLEMENTED']
