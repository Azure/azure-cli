# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import ipaddress
import json
import re
import uuid
from os.path import exists

from azure.cli.core.commands.client_factory import get_mgmt_service_client, get_subscription_id
from azure.cli.command_modules.aro.aaz.latest.network.vnet.subnet import Show as subnet_show
from azure.cli.core.profiles import ResourceType
from azure.cli.core.azclierror import CLIInternalError, InvalidArgumentValueError, \
    RequiredArgumentMissingError
from azure.core.exceptions import ResourceNotFoundError, HttpResponseError
from azure.mgmt.core.tools import is_valid_resource_id, parse_resource_id, resource_id
from knack.log import get_logger

logger = get_logger(__name__)


def validate_cidr(key):
    def _validate_cidr(namespace):
        cidr = getattr(namespace, key)
        if cidr is None:
            return
        try:
            ipaddress.IPv4Network(cidr)
        except ValueError as e:
            raise InvalidArgumentValueError(f"Invalid --{key.replace('_', '-')} '{cidr}'.") from e

    return _validate_cidr


def validate_client_id(namespace):
    if namespace.client_id is None:
        return
    try:
        uuid.UUID(namespace.client_id)
    except ValueError as e:
        raise InvalidArgumentValueError(f"Invalid --client-id '{namespace.client_id}'.") from e

    if namespace.client_secret is None or not str(namespace.client_secret):
        raise RequiredArgumentMissingError('Must specify --client-secret with --client-id.')


def validate_client_secret(isCreate):
    def _validate_client_secret(namespace):
        if not isCreate or namespace.client_secret is None:
            return
        if namespace.client_id is None or not str(namespace.client_id):
            raise RequiredArgumentMissingError('Must specify --client-id with --client-secret.')

    return _validate_client_secret


def validate_cluster_resource_group(cmd, namespace):
    if namespace.cluster_resource_group is None:
        return
    client = get_mgmt_service_client(
        cmd.cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES)

    if client.resource_groups.check_existence(namespace.cluster_resource_group):
        raise InvalidArgumentValueError(
            f"Invalid --cluster-resource-group '{namespace.cluster_resource_group}':"
            " resource group must not exist.")


def validate_disk_encryption_set(cmd, namespace):
    if namespace.disk_encryption_set is None:
        return
    if not is_valid_resource_id(namespace.disk_encryption_set):
        raise InvalidArgumentValueError(
            f"Invalid --disk-encryption-set '{namespace.disk_encryption_set}', has to be a resource ID.")

    desid = parse_resource_id(namespace.disk_encryption_set)
    compute_client = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_COMPUTE)
    try:
        compute_client.disk_encryption_sets.get(resource_group_name=desid['resource_group'],
                                                disk_encryption_set_name=desid['name'])
    except HttpResponseError as err:
        raise InvalidArgumentValueError(
            f"Invalid --disk-encryption-set, error when getting '{namespace.disk_encryption_set}':"
            f" {str(err)}") from err


def validate_domain(namespace):
    if namespace.domain is None:
        return
    if not re.match(r'^' +
                    r'([a-z0-9]|[a-z0-9][-a-z0-9]{0,61}[a-z0-9])' +
                    r'(\.([a-z0-9]|[a-z0-9][-a-z0-9]{0,61}[a-z0-9]))*' +
                    r'$', namespace.domain):
        raise InvalidArgumentValueError(f"Invalid --domain '{namespace.domain}'.")


def validate_pull_secret(namespace):
    if namespace.pull_secret is None:
        # TODO: add aka.ms link here
        warning = "No --pull-secret provided: cluster will not include samples or operators from " + \
            "Red Hat or from certified partners."

        logger.warning(warning)
        return

    try:
        if exists(namespace.pull_secret):
            with open(namespace.pull_secret, 'r', encoding='utf-8') as file:
                namespace.pull_secret = file.read().rstrip('\n')

        if not isinstance(json.loads(namespace.pull_secret), dict):
            raise Exception()  # pylint: disable=broad-exception-raised
    except Exception as e:
        raise InvalidArgumentValueError("Invalid --pull-secret.") from e


def validate_outbound_type(namespace):
    outbound_type = getattr(namespace, 'outbound_type')
    if outbound_type not in {'UserDefinedRouting', 'Loadbalancer', None}:
        raise InvalidArgumentValueError('Invalid --outbound-type: must be "UserDefinedRouting" or "Loadbalancer"')

    ingress_visibility = getattr(namespace, 'ingress_visibility')
    apiserver_visibility = getattr(namespace, 'apiserver_visibility')

    if (outbound_type == 'UserDefinedRouting' and
            (is_visibility_public(ingress_visibility) or is_visibility_public(apiserver_visibility))):
        raise InvalidArgumentValueError('Invalid --outbound-type: cannot use UserDefinedRouting when ' +
                                        'either --apiserver-visibility or --ingress-visibility is set ' +
                                        'to Public or not defined')


def is_visibility_public(visibility):
    return visibility == 'Public' or visibility is None


def validate_subnet(key):
    def _validate_subnet(cmd, namespace):
        subnet = getattr(namespace, key)

        if not is_valid_resource_id(subnet):
            if not namespace.vnet:
                raise RequiredArgumentMissingError(f"Must specify --vnet if --{key.replace('_', '-')} is not an id.")

            validate_vnet(cmd, namespace)

            subnet = namespace.vnet + '/subnets/' + subnet
            setattr(namespace, key, subnet)

        parts = parse_resource_id(subnet)

        if parts['subscription'] != get_subscription_id(cmd.cli_ctx):
            raise InvalidArgumentValueError(
                f"--{key.replace('_', '-')} subscription '{parts['subscription']}' must equal cluster subscription.")

        expected_namespace = 'microsoft.network'
        if parts['namespace'].lower() != expected_namespace:
            raise InvalidArgumentValueError(
                f"--{key.replace('_', '-')} namespace '{parts['namespace']}' must equal Microsoft.Network.")

        expected_type = 'virtualnetworks'
        if parts['type'].lower() != expected_type:
            raise InvalidArgumentValueError(
                f"--{key.replace('_', '-')} type '{parts['type']}' must equal virtualNetworks.")

        expected_last_child_num = 1
        if parts['last_child_num'] != expected_last_child_num:
            raise InvalidArgumentValueError(f"--{key.replace('_', '-')} '{subnet}' must have one child.")

        if 'child_namespace_1' in parts:
            raise InvalidArgumentValueError(f"--{key.replace('_', '-')} '{subnet}' must not have child namespace.")

        if parts['child_type_1'].lower() != 'subnets':
            raise InvalidArgumentValueError(f"--{key.replace('_', '-')} child type '{subnet}' must equal subnets.")

        try:
            subnet_show(cli_ctx=cmd.cli_ctx)(command_args={
                "name": parts['child_name_1'],
                "vnet_name": parts['name'],
                "resource_group": parts['resource_group']
            })
        except Exception as err:
            if isinstance(err, ResourceNotFoundError):
                raise InvalidArgumentValueError(
                    f"Invalid --{key.replace('_', '-')}, error when getting '{subnet}': {str(err)}") from err
            raise CLIInternalError(f"Unexpected error when getting subnet '{subnet}': {str(err)}") from err

    return _validate_subnet


def validate_subnets(master_subnet, worker_subnet):
    master_parts = parse_resource_id(master_subnet)
    worker_parts = parse_resource_id(worker_subnet)

    if master_parts['resource_group'].lower() != worker_parts['resource_group'].lower():
        raise InvalidArgumentValueError(f"--master-subnet resource group '{master_parts['resource_group']}' must equal "
                                        f"--worker-subnet resource group '{worker_parts['resource_group']}'.")

    if master_parts['name'].lower() != worker_parts['name'].lower():
        raise InvalidArgumentValueError(
            f"--master-subnet vnet name '{master_parts['name']}'"
            f" must equal --worker-subnet vnet name '{worker_parts['name']}'.")

    if master_parts['child_name_1'].lower() == worker_parts['child_name_1'].lower():
        raise InvalidArgumentValueError(
            f"--master-subnet name '{master_parts['child_name_1']}'"
            f" must not equal --worker-subnet name '{worker_parts['child_name_1']}'.")


def validate_visibility(key):
    def _validate_visibility(namespace):
        visibility = getattr(namespace, key)
        if visibility is None:
            return
        visibility = visibility.capitalize()

        possible_visibilities = ['Private', 'Public']
        if visibility not in possible_visibilities:
            raise InvalidArgumentValueError(f"Invalid --{key.replace('_', '-')} '{visibility}'.")

    return _validate_visibility


def validate_vnet(cmd, namespace):
    validate_vnet_resource_group_name(namespace)

    if not namespace.vnet:
        return
    if not is_valid_resource_id(namespace.vnet):
        namespace.vnet = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx),
            resource_group=namespace.vnet_resource_group_name,
            namespace='Microsoft.Network',
            type='virtualNetworks',
            name=namespace.vnet,
        )


def validate_vnet_resource_group_name(namespace):
    if not namespace.vnet_resource_group_name:
        namespace.vnet_resource_group_name = namespace.resource_group_name


def validate_worker_count(namespace):
    if not namespace.worker_count:
        return

    minimum_workers_count = 3
    if namespace.worker_count < minimum_workers_count:
        raise InvalidArgumentValueError('--worker-count must be greater than or equal to ' + str(minimum_workers_count))


def validate_worker_vm_disk_size_gb(namespace):
    if not namespace.worker_vm_disk_size_gb:
        return

    minimum_worker_vm_disk_size_gb = 128
    if namespace.worker_vm_disk_size_gb < minimum_worker_vm_disk_size_gb:
        error_msg = '--worker-vm-disk-size-gb must be greater than or equal to ' + str(minimum_worker_vm_disk_size_gb)

        raise InvalidArgumentValueError(error_msg)


def validate_refresh_cluster_credentials(namespace):
    if not namespace.refresh_cluster_credentials:
        return
    if namespace.client_secret is not None or namespace.client_id is not None:
        raise RequiredArgumentMissingError('--client-id and --client-secret must be not set with --refresh-credentials.')  # pylint: disable=line-too-long


def validate_version_format(namespace):
    if namespace.version is not None and not re.match(r'^[4-9]{1}\.[0-9]{1,2}\.[0-9]{1,2}$', namespace.version):
        raise InvalidArgumentValueError('--version is invalid')


def validate_load_balancer_managed_outbound_ip_count(namespace):
    if namespace.load_balancer_managed_outbound_ip_count is None:
        return

    minimum_managed_outbound_ips = 1
    maximum_managed_outbound_ips = 20
    if namespace.load_balancer_managed_outbound_ip_count < minimum_managed_outbound_ips or namespace.load_balancer_managed_outbound_ip_count > maximum_managed_outbound_ips:  # pylint: disable=line-too-long
        error_msg = f"--load-balancer-managed-outbound-ip-count must be between {minimum_managed_outbound_ips} and {maximum_managed_outbound_ips} (inclusive)."  # pylint: disable=line-too-long
        raise InvalidArgumentValueError(error_msg)
