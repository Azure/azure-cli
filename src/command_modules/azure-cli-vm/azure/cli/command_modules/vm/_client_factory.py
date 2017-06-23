# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def _compute_client_factory(**_):
    from azure.cli.core.profiles import ResourceType
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(ResourceType.MGMT_COMPUTE)


def cf_ni(_):
    from azure.cli.core.profiles import ResourceType
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    # TODO: Remove hard coded api-version once
    # https://github.com/Azure/azure-rest-api-specs/issues/570
    # is fixed.
    ni = get_mgmt_service_client(ResourceType.MGMT_NETWORK).network_interfaces
    ni.api_version = '2016-03-30'
    return ni


def cf_avail_set(_):
    return _compute_client_factory().availability_sets


def cf_vm(_):
    return _compute_client_factory().virtual_machines


def cf_vm_ext(_):
    return _compute_client_factory().virtual_machine_extensions


def cf_vm_ext_image(_):
    return _compute_client_factory().virtual_machine_extension_images


def cf_vm_image(_):
    return _compute_client_factory().virtual_machine_images


def cf_usage(_):
    return _compute_client_factory().usage


def cf_vmss(_):
    return _compute_client_factory().virtual_machine_scale_sets


def cf_vmss_vm(_):
    return _compute_client_factory().virtual_machine_scale_set_vms


def cf_vm_sizes(_):
    return _compute_client_factory().virtual_machine_sizes


def cf_disks(_):
    return _compute_client_factory().disks


def cf_snapshots(_):
    return _compute_client_factory().snapshots


def cf_images(_):
    return _compute_client_factory().images
