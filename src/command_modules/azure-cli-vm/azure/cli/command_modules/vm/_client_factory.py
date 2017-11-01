# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def _compute_client_factory(cli_ctx, **_):
    from azure.cli.core.profiles import ResourceType
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_COMPUTE)


def cf_ni(cli_ctx, _):
    from azure.cli.core.profiles import ResourceType
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    # TODO: Remove hard coded api-version once
    # https://github.com/Azure/azure-rest-api-specs/issues/570
    # is fixed.
    ni = get_mgmt_service_client(cli_ctx, ResourceType.MGMT_NETWORK).network_interfaces
    ni.api_version = '2016-03-30'
    return ni


def cf_public_ip_addresses():
    from azure.cli.core.profiles import ResourceType
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    public_ip_ops = get_mgmt_service_client(cli_ctx, ResourceType.MGMT_NETWORK).public_ip_addresses
    return public_ip_ops


def cf_avail_set(cli_ctx, _):
    return _compute_client_factory().availability_sets


def cf_vm(cli_ctx, _):
    return _compute_client_factory().virtual_machines


def cf_vm_ext(cli_ctx, _):
    return _compute_client_factory().virtual_machine_extensions


def cf_vm_ext_image(cli_ctx, _):
    return _compute_client_factory().virtual_machine_extension_images


def cf_vm_image(cli_ctx, _):
    return _compute_client_factory().virtual_machine_images


def cf_usage(cli_ctx, _):
    return _compute_client_factory().usage


def cf_vmss(cli_ctx, _):
    return _compute_client_factory().virtual_machine_scale_sets


def cf_vmss_vm(cli_ctx, _):
    return _compute_client_factory().virtual_machine_scale_set_vms


def cf_vm_sizes(cli_ctx, _):
    return _compute_client_factory().virtual_machine_sizes


def cf_disks(cli_ctx, _):
    return _compute_client_factory().disks


def cf_snapshots(cli_ctx, _):
    return _compute_client_factory().snapshots


def cf_images(cli_ctx, _):
    return _compute_client_factory().images


def cf_run_commands(cli_ctx, _):
    return _compute_client_factory().virtual_machine_run_commands


def cf_rolling_upgrade_commands(cli_ctx, _):
    return _compute_client_factory().virtual_machine_scale_set_rolling_upgrades
