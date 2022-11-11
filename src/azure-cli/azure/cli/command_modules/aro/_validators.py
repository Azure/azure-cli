# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import ipaddress
import json
import re
import uuid

from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.core.commands.client_factory import get_subscription_id
from azure.cli.core.profiles import ResourceType
from azure.cli.core.azclierror import CLIInternalError, InvalidArgumentValueError, \
    RequiredArgumentMissingError
from azure.core.exceptions import ResourceNotFoundError
from knack.log import get_logger
from msrestazure.azure_exceptions import CloudError
from msrestazure.tools import is_valid_resource_id
from msrestazure.tools import parse_resource_id
from msrestazure.tools import resource_id

logger = get_logger(__name__)


def validate_cidr(key):
    def _validate_cidr(namespace):
        cidr = getattr(namespace, key)
        if cidr is not None:
            try:
                ipaddress.IPv4Network(cidr)
            except ValueError as e:
                raise InvalidArgumentValueError(f"Invalid --{key.replace('_', '-')} '{cidr}'.") from e

    return _validate_cidr


def validate_client_id(namespace):
    if namespace.client_id is not None:
        try:
            uuid.UUID(namespace.client_id)
        except ValueError as e:
            raise InvalidArgumentValueError(f"Invalid --client-id '{namespace.client_id}'.") from e

        if namespace.client_secret is None or not str(namespace.client_secret):
            raise RequiredArgumentMissingError('Must specify --client-secret with --client-id.')


def validate_client_secret(isCreate):
    def _validate_client_secret(namespace):
        if isCreate and namespace.client_secret is not None:
            if namespace.client_id is None or not str(namespace.client_id):
                raise RequiredArgumentMissingError('Must specify --client-id with --client-secret.')

    return _validate_client_secret


def validate_cluster_resource_group(cmd, namespace):
    if namespace.cluster_resource_group is not None:
        client = get_mgmt_service_client(
            cmd.cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES)

        if client.resource_groups.check_existence(namespace.cluster_resource_group):
            raise InvalidArgumentValueError(
                f"Invalid --cluster-resource-group '{namespace.cluster_resource_group}':"
                " resource group must not exist.")


def validate_disk_encryption_set(cmd, namespace):
    if namespace.disk_encryption_set is not None:
        if not is_valid_resource_id(namespace.disk_encryption_set):
            raise InvalidArgumentValueError(
                f"Invalid --disk-encryption-set '{namespace.disk_encryption_set}', has to be a resource ID.")

        desid = parse_resource_id(namespace.disk_encryption_set)
        compute_client = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_COMPUTE)
        try:
            compute_client.disk_encryption_sets.get(resource_group_name=desid['resource_group'],
                                                    disk_encryption_set_name=desid['name'])
        except CloudError as err:
            raise InvalidArgumentValueError(
                f"Invald --disk-encryption-set, error when getting '{namespace.disk_encryption_set}':"
                f" {str(err)}") from err


def validate_domain(namespace):
    if namespace.domain is not None:
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

    else:
        try:
            if not isinstance(json.loads(namespace.pull_secret), dict):
                raise Exception()
        except Exception as e:
            raise InvalidArgumentValueError("Invalid --pull-secret.") from e


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

        if parts['namespace'].lower() != 'microsoft.network':
            raise InvalidArgumentValueError(
                f"--{key.replace('_', '-')} namespace '{parts['namespace']}' must equal Microsoft.Network.")

        if parts['type'].lower() != 'virtualnetworks':
            raise InvalidArgumentValueError(
                f"--{key.replace('_', '-')} type '{parts['type']}' must equal virtualNetworks.")

        if parts['last_child_num'] != 1:
            raise InvalidArgumentValueError(f"--{key.replace('_', '-')} '{subnet}' must have one child.")

        if 'child_namespace_1' in parts:
            raise InvalidArgumentValueError(f"--{key.replace('_', '-')} '{subnet}' must not have child namespace.")

        if parts['child_type_1'].lower() != 'subnets':
            raise InvalidArgumentValueError(f"--{key.replace('_', '-')} child type '{subnet}' must equal subnets.")

        client = get_mgmt_service_client(
            cmd.cli_ctx, ResourceType.MGMT_NETWORK)
        try:
            client.subnets.get(parts['resource_group'],
                               parts['name'], parts['child_name_1'])
        except Exception as err:
            if isinstance(err, ResourceNotFoundError):
                raise InvalidArgumentValueError(
                    f"Invald --{key.replace('_', '-')}, error when getting '{subnet}': {str(err)}") from err
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
        if visibility is not None:
            visibility = visibility.capitalize()
            if visibility not in ['Private', 'Public']:
                raise InvalidArgumentValueError(f"Invalid --{key.replace('_', '-')} '{visibility}'.")

    return _validate_visibility


def validate_vnet(cmd, namespace):
    validate_vnet_resource_group_name(namespace)

    if namespace.vnet:
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
    if namespace.worker_count:
        if namespace.worker_count < 3:
            raise InvalidArgumentValueError('--worker-count must be greater than or equal to 3.')


def validate_worker_vm_disk_size_gb(namespace):
    if namespace.worker_vm_disk_size_gb:
        if namespace.worker_vm_disk_size_gb < 128:
            raise InvalidArgumentValueError('--worker-vm-disk-size-gb must be greater than or equal to 128.')


def validate_refresh_cluster_credentials(namespace):
    if namespace.refresh_cluster_credentials:
        if namespace.client_secret is not None or namespace.client_id is not None:
            raise RequiredArgumentMissingError('--client-id and --client-secret must be not set with --refresh-credentials.')  # pylint: disable=line-too-long
