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
from knack.log import get_logger
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
            except ValueError:
                raise InvalidArgumentValueError("Invalid --%s '%s'." %
                                                (key.replace('_', '-'), cidr))

    return _validate_cidr


def validate_client_id(namespace):
    if namespace.client_id is not None:
        try:
            uuid.UUID(namespace.client_id)
        except ValueError:
            raise InvalidArgumentValueError("Invalid --client-id '%s'." % namespace.client_id)

        if namespace.client_secret is None or not str(namespace.client_secret):
            raise RequiredArgumentMissingError('Must specify --client-secret with --client-id.')


def validate_client_secret(namespace):
    if namespace.client_secret is not None:
        if namespace.client_id is None or not str(namespace.client_id):
            raise RequiredArgumentMissingError('Must specify --client-id with --client-secret.')


def validate_cluster_resource_group(cmd, namespace):
    if namespace.cluster_resource_group is not None:
        client = get_mgmt_service_client(
            cmd.cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES)

        if client.resource_groups.check_existence(namespace.cluster_resource_group):
            raise InvalidArgumentValueError(
                "Invalid --cluster-resource-group '%s': resource group must not exist." %
                namespace.cluster_resource_group)


def validate_domain(namespace):
    if namespace.domain is not None:
        if not re.match(r'^' +
                        r'([a-z0-9]|[a-z0-9][-a-z0-9]{0,61}[a-z0-9])' +
                        r'(\.([a-z0-9]|[a-z0-9][-a-z0-9]{0,61}[a-z0-9]))*' +
                        r'$', namespace.domain):
            raise InvalidArgumentValueError("Invalid --domain '%s'." %
                                            namespace.domain)


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
        except:
            raise InvalidArgumentValueError("Invalid --pull-secret.")


def validate_subnet(key):
    def _validate_subnet(cmd, namespace):
        from azure.core.exceptions import HttpResponseError
        subnet = getattr(namespace, key)

        if not is_valid_resource_id(subnet):
            if not namespace.vnet:
                raise RequiredArgumentMissingError('Must specify --vnet if --%s is not an id.' %
                                                   key.replace('_', '-'))

            validate_vnet(cmd, namespace)

            subnet = namespace.vnet + '/subnets/' + subnet
            setattr(namespace, key, subnet)

        parts = parse_resource_id(subnet)

        if parts['subscription'] != get_subscription_id(cmd.cli_ctx):
            raise InvalidArgumentValueError("--%s subscription '%s' must equal cluster subscription." %
                                            (key.replace('_', '-'), parts["subscription"]))

        if parts['namespace'].lower() != 'microsoft.network':
            raise InvalidArgumentValueError("--%s namespace '%s' must equal Microsoft.Network." %
                                            (key.replace('_', '-'), parts["namespace"]))

        if parts['type'].lower() != 'virtualnetworks':
            raise InvalidArgumentValueError("--%s type '%s' must equal virtualNetworks." %
                                            (key.replace('_', '-'), parts["type"]))

        if parts['last_child_num'] != 1:
            raise InvalidArgumentValueError("--%s '%s' must have one child." %
                                            (key.replace('_', '-'), subnet))

        if 'child_namespace_1' in parts:
            raise InvalidArgumentValueError("--%s '%s' must not have child namespace." %
                                            (key.replace('_', '-'), subnet))

        if parts['child_type_1'].lower() != 'subnets':
            raise InvalidArgumentValueError("--%s child type '%s' must equal subnets." %
                                            (key.replace('_', '-'), subnet))

        client = get_mgmt_service_client(
            cmd.cli_ctx, ResourceType.MGMT_NETWORK)
        try:
            client.subnets.get(parts['resource_group'],
                               parts['name'], parts['child_name_1'])
        except HttpResponseError as err:
            raise CLIInternalError(err.message)

    return _validate_subnet


def validate_subnets(master_subnet, worker_subnet):
    master_parts = parse_resource_id(master_subnet)
    worker_parts = parse_resource_id(worker_subnet)

    if master_parts['resource_group'].lower() != worker_parts['resource_group'].lower():
        raise InvalidArgumentValueError("--master-subnet resource group '%s' must equal "
                                        "--worker-subnet resource group '%s'." %
                                        (master_parts['resource_group'], worker_parts['resource_group']))

    if master_parts['name'].lower() != worker_parts['name'].lower():
        raise InvalidArgumentValueError("--master-subnet vnet name '%s' must equal --worker-subnet vnet name '%s'." %
                                        (master_parts['name'], worker_parts['name']))

    if master_parts['child_name_1'].lower() == worker_parts['child_name_1'].lower():
        raise InvalidArgumentValueError("--master-subnet name '%s' must not equal --worker-subnet name '%s'." %
                                        (master_parts['child_name_1'], worker_parts['child_name_1']))

    return resource_id(
        subscription=master_parts['subscription'],
        resource_group=master_parts['resource_group'],
        namespace='Microsoft.Network',
        type='virtualNetworks',
        name=master_parts['name'],
    )


def validate_visibility(key):
    def _validate_visibility(namespace):
        visibility = getattr(namespace, key)
        if visibility is not None:
            visibility = visibility.capitalize()
            if visibility not in ['Private', 'Public']:
                raise InvalidArgumentValueError("Invalid --%s '%s'." %
                                                (key.replace('_', '-'), visibility))

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
