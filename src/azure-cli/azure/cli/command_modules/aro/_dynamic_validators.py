# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


import ipaddress
import re
from itertools import tee

from azure.cli.command_modules.aro._validators import validate_vnet, validate_cidr
from azure.cli.command_modules.aro._rbac import has_role_assignment_on_resource
from azure.cli.command_modules.aro.aaz.latest.network.vnet.subnet import Show as subnet_show
from azure.cli.command_modules.aro.aaz.latest.network.vnet import Show as vnet_show
from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.core.commands.validators import get_default_location_from_resource_group
from azure.cli.core.profiles import ResourceType
from azure.cli.core.azclierror import CLIInternalError, InvalidArgumentValueError, \
    RequiredArgumentMissingError
from azure.core.exceptions import ResourceNotFoundError, HttpResponseError
from azure.mgmt.core.tools import is_valid_resource_id, parse_resource_id
from knack.log import get_logger
import azure.cli.command_modules.aro.custom


logger = get_logger(__name__)
log_entry_type = {'warn': 'Warning', 'error': 'Error'}


def can_do_action(perms, action):
    for perm in perms:
        matched = False

        for perm_action in perm.actions:
            match = re.escape(perm_action)
            match = re.match("(?i)^" + match.replace(r"\*", ".*") + "$", action)
            if match:
                matched = True
                break

        if not matched:
            continue

        for not_action in perm.not_actions:
            match = re.escape(not_action)
            match = re.match("(?i)^" + match.replace(r"\*", ".*") + "$", action)
            if match:
                matched = False
                break

        if matched:
            return True

    return False


def validate_resource(client, key, resource, actions):
    perms = client.permissions.list_for_resource(resource['resource_group'],
                                                 resource['namespace'],
                                                 "",
                                                 resource['type'],
                                                 resource['name'])
    errors = []
    for action in actions:
        perms, perms_copy = tee(perms)
        perms_list = list(perms_copy)
        if not can_do_action(perms_list, action):
            row = [key, resource['name'], log_entry_type["error"], f"{action} permission is missing"]
            errors.append(row)

    return errors


def get_subnet(cli_ctx, key, subnet, subnet_parts):
    try:
        subnet_obj = subnet_show(cli_ctx=cli_ctx)(command_args={
            'resource_group': subnet_parts['resource_group'],
            'name': subnet_parts['child_name_1'],
            'vnet_name': subnet_parts['name']
        })
    except ResourceNotFoundError as err:
        raise InvalidArgumentValueError(
            f"Invalid --{key.replace('_', '-')}, error when getting '{subnet}': {str(err)}") from err

    except Exception as err:
        raise CLIInternalError(
            f"Unexpected error when getting subnet '{subnet}': {str(err)}") from err

    return subnet_obj


def get_vnet(cli_ctx, key, vnet, vnet_parts):
    try:
        vnet_obj = vnet_show(cli_ctx=cli_ctx)(command_args={
            'name': vnet_parts['name'],
            'resource_group': vnet_parts['resource_group']
        })
    except ResourceNotFoundError as err:
        raise InvalidArgumentValueError(
            f"Invalid --{key.replace('_', '-')}, error when getting '{vnet}': {str(err)}") from err
    except Exception as err:
        raise CLIInternalError(
            f"Unexpected error when getting vnet '{vnet}': {str(err)}") from err

    return vnet_obj


def get_clients(key, cmd):
    parts = parse_resource_id(key)

    auth_client = get_mgmt_service_client(
        cmd.cli_ctx, ResourceType.MGMT_AUTHORIZATION, api_version="2015-07-01")

    return parts, auth_client


# Function to create a progress tracker decorator for the dynamic validation functions
def get_progress_tracker(msg):
    def progress_tracking(func):
        def inner(cmd, namespace):
            hook = cmd.cli_ctx.get_progress_controller()
            hook.add(message=msg)

            errors = func(cmd, namespace)

            hook.end()

            return errors
        return inner
    return progress_tracking


# Validating that the virtual network has the correct permissions
def dyn_validate_vnet(key):
    prog = get_progress_tracker("Validating Virtual Network Permissions")

    @prog
    def _validate_vnet(cmd, namespace):
        errors = []

        vnet = getattr(namespace, key)

        if not is_valid_resource_id(vnet):
            raise RequiredArgumentMissingError(
                f"Must specify --vnet if --{key.replace('_', '-')} is not an id.")

        validate_vnet(cmd, namespace)

        parts, auth_client = get_clients(vnet, cmd)

        get_vnet(cmd.cli_ctx, key, vnet, parts)

        errors = validate_resource(auth_client, key, parts, [
            "Microsoft.Network/virtualNetworks/join/action",
            "Microsoft.Network/virtualNetworks/read",
            "Microsoft.Network/virtualNetworks/write",
            "Microsoft.Network/virtualNetworks/subnets/join/action",
            "Microsoft.Network/virtualNetworks/subnets/read",
            "Microsoft.Network/virtualNetworks/subnets/write", ])

        return errors

    return _validate_vnet


# Validating that the route tables attached to the subnet have the
# correct permissions and that the subnet is not assigned to an NSG
def dyn_validate_subnet_and_route_tables(key):
    prog = get_progress_tracker(f"Validating {key} permissions")

    @prog
    def _validate_subnet(cmd, namespace):
        errors = []

        subnet = getattr(namespace, key)

        if not is_valid_resource_id(subnet):
            if not namespace.vnet:
                raise RequiredArgumentMissingError(
                    f"Must specify --vnet if --{key.replace('_', '-')} is not an id.")

            validate_vnet(cmd, namespace)

            subnet = namespace.vnet + '/subnets/' + subnet
            setattr(namespace, key, subnet)

        parts, auth_client = get_clients(subnet, cmd)

        subnet_obj = get_subnet(cmd.cli_ctx, key, subnet, parts)

        if subnet_obj.get('routeTable', None):
            route_parts = parse_resource_id(subnet_obj['routeTable']['id'])

            errors = validate_resource(auth_client, f"{key}_route_table", route_parts, [
                "Microsoft.Network/routeTables/join/action",
                "Microsoft.Network/routeTables/read",
                "Microsoft.Network/routeTables/write"])

        if not namespace.enable_preconfigured_nsg and subnet_obj.get('networkSecurityGroup', None):
            message = f"A Network Security Group \"{subnet_obj['networkSecurityGroup']['id']}\" "\
                      "is already assigned to this subnet. Ensure there are no Network "\
                      "Security Groups assigned to cluster subnets before cluster creation"
            error = [key, parts['child_name_1'], log_entry_type["error"], message]
            errors.append(error)

        return errors

    return _validate_subnet


# Validating that the cidr ranges between the master_subnet, worker_subnet,
# service_cidr and pod_cidr do not overlap at all
def dyn_validate_cidr_ranges():
    prog = get_progress_tracker("Validating no overlapping CIDR Ranges on subnets")

    @prog
    def _validate_cidr_ranges(cmd, namespace):
        MIN_CIDR_PREFIX = 23

        addresses = []

        ERROR_KEY = "CIDR Range"
        master_subnet = namespace.master_subnet
        worker_subnet = namespace.worker_subnet
        pod_cidr = namespace.pod_cidr
        service_cidr = namespace.service_cidr

        worker_parts = parse_resource_id(worker_subnet)
        master_parts = parse_resource_id(master_subnet)

        fn = validate_cidr("pod_cidr")
        fn(namespace)
        fn = validate_cidr("service_cidr")
        fn(namespace)

        cidr_array = {}

        if pod_cidr is not None:
            node_mask = MIN_CIDR_PREFIX - int(pod_cidr.split("/")[1])
            if node_mask < 2:
                addresses.append(["Pod CIDR",
                                  "Pod CIDR Capacity",
                                  log_entry_type["error"],
                                  f"{pod_cidr} does not contain enough addresses for 3 master nodes " +
                                  "(Requires cidr prefix of 21 or lower)"])
            cidr_array["Pod CIDR"] = ipaddress.IPv4Network(pod_cidr)
        if service_cidr is not None:
            cidr_array["Service CIDR"] = ipaddress.IPv4Network(service_cidr)

        worker_subnet_obj = get_subnet(
            cmd.cli_ctx, None, worker_subnet, worker_parts)

        if worker_subnet_obj.get('addressPrefix', None) is None:
            for address in worker_subnet_obj.get('addressPrefixes'):
                cidr_array["Worker Subnet CIDR -- " +
                           address] = ipaddress.IPv4Network(address)
        else:
            cidr_array["Worker Subnet CIDR"] = ipaddress.IPv4Network(
                worker_subnet_obj.get('addressPrefix'))

        master_subnet_obj = get_subnet(
            cmd.cli_ctx, None, master_subnet, master_parts)

        if master_subnet_obj.get('addressPrefix', None) is None:
            for address in master_subnet_obj.get('addressPrefixes'):
                cidr_array["Master Subnet CIDR -- " +
                           address] = ipaddress.IPv4Network(address)
        else:
            cidr_array["Master Subnet CIDR"] = ipaddress.IPv4Network(
                master_subnet_obj.get('addressPrefix'))

        ipv4_zero = ipaddress.IPv4Network("0.0.0.0/0")

        for item in cidr_array.items():
            key = item[0]
            cidr = item[1]
            if not cidr.overlaps(ipv4_zero):
                addresses.append([ERROR_KEY, key, log_entry_type["error"],
                                  f"{cidr} is not valid as it does not overlap with {ipv4_zero}"])
            for item2 in cidr_array.items():
                compare = item2[1]
                if cidr is not compare:
                    if cidr.overlaps(compare):
                        addresses.append([ERROR_KEY, key, log_entry_type["error"],
                                          f"{cidr} is not valid as it overlaps with {compare}"])

        return addresses

    return _validate_cidr_ranges


def dyn_validate_resource_permissions(service_principle_ids, resources):
    prog = get_progress_tracker("Validating resource permissions")

    @prog
    def _validate_resource_permissions(cmd,
                                       _namespace):
        errors = []

        for sp_id in service_principle_ids:
            for role in sorted(resources):
                for resource in resources[role]:
                    try:
                        resource_contributor_exists = has_role_assignment_on_resource(cmd.cli_ctx,
                                                                                      resource,
                                                                                      sp_id,
                                                                                      role)
                        if not resource_contributor_exists:
                            parts = parse_resource_id(resource)
                            errors.append(["Resource Permissions",
                                           parts['type'],
                                           log_entry_type["warn"],
                                           f"Resource {parts['name']} is missing role assignment " +
                                           f"{role} for service principal {sp_id} " +
                                           "(These roles will be automatically added during cluster creation)"])
                    except HttpResponseError as e:
                        logger.error(e.message)
                        raise
        return errors
    return _validate_resource_permissions


def dyn_validate_version():
    prog = get_progress_tracker("Validating OpenShift Version")

    @prog
    def _validate_version(cmd,
                          namespace):
        errors = []

        if namespace.location is None:
            get_default_location_from_resource_group(cmd, namespace)

        versions = azure.cli.command_modules.aro.custom.aro_get_versions(namespace.client, namespace.location)

        found = False
        for version in versions:
            if version == namespace.version:
                found = True
                break

        if not found:
            errors.append(["OpenShift Version",
                           namespace.version,
                           log_entry_type["error"],
                           f"{namespace.version} is not a valid version, valid versions are {versions}"])

        return errors
    return _validate_version


def validate_cluster_create(version,
                            resources,
                            service_principle_ids):
    error_object = []

    error_object.append(dyn_validate_vnet("vnet"))
    error_object.append(dyn_validate_subnet_and_route_tables("master_subnet"))
    error_object.append(dyn_validate_subnet_and_route_tables("worker_subnet"))
    error_object.append(dyn_validate_cidr_ranges())
    error_object.append(dyn_validate_resource_permissions(service_principle_ids, resources))
    if version is not None:
        error_object.append(dyn_validate_version())

    return error_object
