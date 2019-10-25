# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from distutils.version import StrictVersion  # pylint: disable=no-name-in-module,import-error
# pylint: disable=no-name-in-module,import-error
from azure.mgmt.containerservice.v2019_08_01.models import ManagedClusterAPIServerAccessProfile


def _populate_api_server_access_profile(api_server_authorized_ip_ranges, instance=None):
    if instance is None or instance.api_server_access_profile is None:
        profile = ManagedClusterAPIServerAccessProfile()
    else:
        profile = instance.api_server_access_profile

    if api_server_authorized_ip_ranges == "":
        authorized_ip_ranges = []
    else:
        authorized_ip_ranges = [ip.strip() for ip in api_server_authorized_ip_ranges.split(",")]

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
