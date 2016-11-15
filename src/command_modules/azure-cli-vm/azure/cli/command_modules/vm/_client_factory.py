# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

def _compute_client_factory(**_):
    from azure.mgmt.compute import ComputeManagementClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(ComputeManagementClient)

def _subscription_client_factory(**_):
    from azure.mgmt.resource.subscriptions import SubscriptionClient
    from azure.cli.core.commands.client_factory import get_subscription_service_client
    return get_subscription_service_client(SubscriptionClient)

def cf_vm_create(_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.cli.command_modules.vm.mgmt_vm.lib import VmCreationClient as VMCreateClient
    client = get_mgmt_service_client(VMCreateClient)
    client.config.long_running_operation_timeout = 5 #seconds
    return client.vm

def cf_ni(_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.network import NetworkManagementClient
    # TODO: Remove hard coded api-version once
    # https://github.com/Azure/azure-rest-api-specs/issues/570
    # is fixed.
    return get_mgmt_service_client(NetworkManagementClient, api_version='2016-03-30').network_interfaces #pylint: disable=line-too-long

def cf_avail_set_create(_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.cli.command_modules.vm.mgmt_avail_set.lib import AvailSetCreationClient as AvailSetCreateClient #pylint: disable=line-too-long
    return get_mgmt_service_client(AvailSetCreateClient).avail_set

def cf_avail_set(_):
    return _compute_client_factory().availability_sets

def cf_acs_create(_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.cli.command_modules.vm.mgmt_acs.lib import AcsCreationClient as AcsCreateClient
    return get_mgmt_service_client(AcsCreateClient).acs

def cf_vmss_create(_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.cli.command_modules.vm.mgmt_vmss.lib import VmssCreationClient as VmssCreateClient
    return get_mgmt_service_client(VmssCreateClient).vmss

def cf_vm(_):
    return _compute_client_factory().virtual_machines

def cf_acs(_):
    return _compute_client_factory().container_services

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

