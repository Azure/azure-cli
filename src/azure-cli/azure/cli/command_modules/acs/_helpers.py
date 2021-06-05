# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from distutils.version import StrictVersion  # pylint: disable=no-name-in-module,import-error
# pylint: disable=no-name-in-module,import-error
from knack.util import CLIError
from azure.cli.core.profiles import ResourceType
from ._consts import CONST_OUTBOUND_TYPE_LOAD_BALANCER, CONST_OUTBOUND_TYPE_USER_DEFINED_ROUTING


def _populate_api_server_access_profile(cmd,
                                        api_server_authorized_ip_ranges,
                                        enable_private_cluster=False, instance=None):
    if instance is None or instance.api_server_access_profile is None:
        ManagedClusterAPIServerAccessProfile = cmd.get_models('ManagedClusterAPIServerAccessProfile',
                                                              resource_type=ResourceType.MGMT_CONTAINERSERVICE,
                                                              operation_group='managed_clusters')
        profile = ManagedClusterAPIServerAccessProfile()
    else:
        profile = instance.api_server_access_profile

    if enable_private_cluster:
        profile.enable_private_cluster = True

    if api_server_authorized_ip_ranges is None or api_server_authorized_ip_ranges == "":
        authorized_ip_ranges = []
    else:
        authorized_ip_ranges = [
            ip.strip() for ip in api_server_authorized_ip_ranges.split(",")]

    if profile.enable_private_cluster and authorized_ip_ranges:
        raise CLIError(
            '--api-server-authorized-ip-ranges is not supported for private cluster')

    profile.authorized_ip_ranges = authorized_ip_ranges
    return profile


def _set_load_balancer_sku(load_balancer_sku, kubernetes_version):
    if load_balancer_sku:
        return load_balancer_sku
    if kubernetes_version and StrictVersion(kubernetes_version) < StrictVersion("1.13.0"):
        print('Setting load_balancer_sku to basic as it is not specified and kubernetes \
        version(%s) less than 1.13.0 only supports basic load balancer SKU\n' % (kubernetes_version))
        return "basic"
    return "standard"


def _set_vm_set_type(vm_set_type, kubernetes_version):
    if not vm_set_type:
        if kubernetes_version and StrictVersion(kubernetes_version) < StrictVersion("1.12.9"):
            print('Setting vm_set_type to availabilityset as it is \
            not specified and kubernetes version(%s) less than 1.12.9 only supports \
            availabilityset\n' % (kubernetes_version))
            vm_set_type = "AvailabilitySet"

    if not vm_set_type:
        vm_set_type = "VirtualMachineScaleSets"

    # normalize as server validation is case-sensitive
    if vm_set_type.lower() == "AvailabilitySet".lower():
        vm_set_type = "AvailabilitySet"

    if vm_set_type.lower() == "VirtualMachineScaleSets".lower():
        vm_set_type = "VirtualMachineScaleSets"
    return vm_set_type


def _set_outbound_type(outbound_type, vnet_subnet_id, load_balancer_sku, load_balancer_profile):
    if outbound_type != CONST_OUTBOUND_TYPE_USER_DEFINED_ROUTING:
        return CONST_OUTBOUND_TYPE_LOAD_BALANCER

    if load_balancer_sku == "basic":
        raise CLIError(
            "userDefinedRouting doesn't support basic load balancer sku")

    if vnet_subnet_id in ["", None]:
        raise CLIError("--vnet-subnet-id must be specified for userDefinedRouting and it must \
        be pre-configured with a route table with egress rules")

    if load_balancer_profile:
        if (load_balancer_profile.managed_outbound_ips or
                load_balancer_profile.outbound_ips or
                load_balancer_profile.outbound_ip_prefixes):
            raise CLIError(
                "userDefinedRouting doesn't support customizing a standard load balancer with IP addresses")

    return CONST_OUTBOUND_TYPE_USER_DEFINED_ROUTING


def _parse_comma_separated_list(text):
    if text is None:
        return None
    if text == "":
        return []
    return text.split(",")
