# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import random

import azure.mgmt.redhatopenshift.models as openshiftcluster

from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.core.commands.client_factory import get_subscription_id
from azure.cli.core.profiles import ResourceType
from azure.cli.core.util import sdk_no_wait
from azure.cli.core.azclierror import ResourceNotFoundError, UnauthorizedError
from azure.cli.command_modules.aro._aad import AADManager
from azure.cli.command_modules.aro._rbac import assign_network_contributor_to_resource, \
    has_network_contributor_on_resource
from azure.cli.command_modules.aro._validators import validate_subnets
from azure.graphrbac.models import GraphErrorException

from knack.log import get_logger

from msrestazure.azure_exceptions import CloudError
from msrestazure.tools import resource_id, parse_resource_id
from msrest.exceptions import HttpOperationError

logger = get_logger(__name__)

FP_CLIENT_ID = 'f1dd0a37-89c6-4e07-bcd1-ffd3d43d8875'


def aro_create(cmd,  # pylint: disable=too-many-locals
               client,
               resource_group_name,
               resource_name,
               master_subnet,
               worker_subnet,
               vnet=None,
               vnet_resource_group_name=None,  # pylint: disable=unused-argument
               location=None,
               pull_secret=None,
               domain=None,
               cluster_resource_group=None,
               client_id=None,
               client_secret=None,
               pod_cidr=None,
               service_cidr=None,
               master_vm_size=None,
               worker_vm_size=None,
               worker_vm_disk_size_gb=None,
               worker_count=None,
               apiserver_visibility=None,
               ingress_visibility=None,
               tags=None,
               no_wait=False):

    resource_client = get_mgmt_service_client(
        cmd.cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES)
    provider = resource_client.providers.get('Microsoft.RedHatOpenShift')
    if provider.registration_state != 'Registered':
        raise UnauthorizedError('Microsoft.RedHatOpenShift provider is not registered.',
                                'Run `az provider register -n Microsoft.RedHatOpenShift --wait`.')

    vnet = validate_subnets(master_subnet, worker_subnet)
    resources = get_network_resources(cmd.cli_ctx, [master_subnet, worker_subnet], vnet)

    subscription_id = get_subscription_id(cmd.cli_ctx)

    random_id = generate_random_id()

    aad = AADManager(cmd.cli_ctx)
    if client_id is None:
        app, client_secret = aad.create_application(cluster_resource_group or 'aro-' + random_id)
        client_id = app.app_id

    client_sp = aad.get_service_principal(client_id)
    if not client_sp:
        client_sp = aad.create_service_principal(client_id)

    rp_client_id = FP_CLIENT_ID
    rp_client_sp = aad.get_service_principal(rp_client_id)
    if not rp_client_sp:
        raise ResourceNotFoundError("RP service principal not found.")

    for sp_id in [client_sp.object_id, rp_client_sp.object_id]:
        for resource in sorted(resources):
            if not has_network_contributor_on_resource(cmd.cli_ctx, resource, sp_id):
                assign_network_contributor_to_resource(cmd.cli_ctx, resource, sp_id)

    worker_vm_size = worker_vm_size or 'Standard_D4s_v3'

    if apiserver_visibility is not None:
        apiserver_visibility = apiserver_visibility.capitalize()

    if ingress_visibility is not None:
        ingress_visibility = ingress_visibility.capitalize()

    oc = openshiftcluster.OpenShiftCluster(
        location=location,
        tags=tags,
        cluster_profile=openshiftcluster.ClusterProfile(
            pull_secret=pull_secret or "",
            domain=domain or random_id,
            resource_group_id='/subscriptions/%s/resourceGroups/%s' %
            (subscription_id, cluster_resource_group or "aro-" + random_id),
        ),
        service_principal_profile=openshiftcluster.ServicePrincipalProfile(
            client_id=client_id,
            client_secret=client_secret,
        ),
        network_profile=openshiftcluster.NetworkProfile(
            pod_cidr=pod_cidr or '10.128.0.0/14',
            service_cidr=service_cidr or '172.30.0.0/16',
        ),
        master_profile=openshiftcluster.MasterProfile(
            vm_size=master_vm_size or 'Standard_D8s_v3',
            subnet_id=master_subnet,
        ),
        worker_profiles=[
            openshiftcluster.WorkerProfile(
                name='worker',  # TODO: 'worker' should not be hard-coded
                vm_size=worker_vm_size,
                disk_size_gb=worker_vm_disk_size_gb or 128,
                subnet_id=worker_subnet,
                count=worker_count or 3,
            )
        ],
        apiserver_profile=openshiftcluster.APIServerProfile(
            visibility=apiserver_visibility or 'Public',
        ),
        ingress_profiles=[
            openshiftcluster.IngressProfile(
                name='default',  # TODO: 'default' should not be hard-coded
                visibility=ingress_visibility or 'Public',
            )
        ],
    )

    return sdk_no_wait(no_wait, client.create_or_update,
                       resource_group_name=resource_group_name,
                       resource_name=resource_name,
                       parameters=oc)


def aro_delete(cmd, client, resource_group_name, resource_name, no_wait=False):
    # TODO: clean up rbac
    rp_client_sp = None
    resources = set()

    try:
        oc = client.get(resource_group_name, resource_name)

        # Get cluster resources we need to assign network contributor on
        resources = get_cluster_network_resources(cmd.cli_ctx, oc)
    except (CloudError, HttpOperationError) as e:
        logger.info(e.message)

    aad = AADManager(cmd.cli_ctx)
    rp_client_id = FP_CLIENT_ID

    # Best effort - assume the role assignments on the SP exist if exception raised
    try:
        rp_client_sp = aad.get_service_principal(rp_client_id)
        if not rp_client_sp:
            raise ResourceNotFoundError("RP service principal not found.")
    except GraphErrorException as e:
        logger.info(e.message)

    # Customers frequently remove the Cluster or RP's service principal permissions.
    # Attempt to fix this before performing any action against the cluster
    if rp_client_sp:
        for resource in sorted(resources):
            # Create the role assignment if it doesn't exist
            # Assume that the role assignment exists if we fail to look it up
            resource_contributor_exists = True

            try:
                resource_contributor_exists = has_network_contributor_on_resource(cmd.cli_ctx, resource,
                                                                                  rp_client_sp.object_id)
            except CloudError as e:
                logger.info(e.message)
                continue

            if not resource_contributor_exists:
                assign_network_contributor_to_resource(cmd.cli_ctx, resource, rp_client_sp.object_id)

    return sdk_no_wait(no_wait, client.delete,
                       resource_group_name=resource_group_name,
                       resource_name=resource_name)


def aro_list(client, resource_group_name=None):
    if resource_group_name:
        return client.list_by_resource_group(resource_group_name)
    return client.list()


def aro_show(client, resource_group_name, resource_name):
    return client.get(resource_group_name, resource_name)


def aro_list_credentials(client, resource_group_name, resource_name):
    return client.list_credentials(resource_group_name, resource_name)


def aro_update(cmd, client, resource_group_name, resource_name, no_wait=False):
    rp_client_sp = None
    client_sp = None
    resources = set()

    try:
        oc = client.get(resource_group_name, resource_name)

        # Get cluster resources we need to assign network contributor on
        resources = get_cluster_network_resources(cmd.cli_ctx, oc)
    except (CloudError, HttpOperationError) as e:
        logger.info(e.message)

    aad = AADManager(cmd.cli_ctx)
    rp_client_id = FP_CLIENT_ID

    # Best effort - assume the role assignments on the SP exist if exception raised
    try:

        rp_client_sp = aad.get_service_principal(rp_client_id)
        if not rp_client_sp:
            raise ResourceNotFoundError("RP service principal not found.")
    except GraphErrorException as e:
        logger.info(e.message)

    client_id = oc.service_principal_profile.client_id

    # Best effort - assume the role assignments on the SP exist if exception raised
    try:
        client_sp = aad.get_service_principal(client_id)
        if not client_sp:
            raise ResourceNotFoundError("Cluster service principal not found.")
    except GraphErrorException as e:
        logger.info(e.message)

    # Drop any None service principal objects
    sp_obj_ids = [sp.object_id for sp in [rp_client_sp, client_sp] if sp]

    # Customers frequently remove the Cluster or RP's service principal permissions.
    # Attempt to fix this before performing any action against the cluster
    for sp_id in sp_obj_ids:
        for resource in sorted(resources):
            # Create the role assignment if it doesn't exist
            # Assume that the role assignment exists if we fail to look it up
            resource_contributor_exists = True

            try:
                resource_contributor_exists = has_network_contributor_on_resource(cmd.cli_ctx, resource, sp_id)
            except CloudError as e:
                logger.info(e.message)
                continue

            if not resource_contributor_exists:
                assign_network_contributor_to_resource(cmd.cli_ctx, resource, sp_id)

    oc = openshiftcluster.OpenShiftClusterUpdate()

    return sdk_no_wait(no_wait, client.update,
                       resource_group_name=resource_group_name,
                       resource_name=resource_name,
                       parameters=oc)


def generate_random_id():
    random_id = (random.choice('abcdefghijklmnopqrstuvwxyz') +
                 ''.join(random.choice('abcdefghijklmnopqrstuvwxyz1234567890')
                         for _ in range(7)))
    return random_id


def get_route_tables_from_subnets(cli_ctx, subnets):
    network_client = get_mgmt_service_client(cli_ctx, ResourceType.MGMT_NETWORK)

    route_tables = set()
    for sn in subnets:
        sid = parse_resource_id(sn)

        subnet = network_client.subnets.get(resource_group_name=sid['resource_group'],
                                            virtual_network_name=sid['name'],
                                            subnet_name=sid['resource_name'])

        if subnet.route_table is not None:
            route_tables.add(subnet.route_table.id)

    return route_tables


def get_cluster_network_resources(cli_ctx, oc):
    master_subnet = oc.master_profile.subnet_id
    worker_subnets = set()

    # Ensure that worker_profiles exists
    # it will not be returned if the cluster resources do not exist
    if oc.worker_profiles is not None:
        worker_subnets = {w.subnet_id for w in oc.worker_profiles if w}

    master_parts = parse_resource_id(master_subnet)
    vnet = resource_id(
        subscription=master_parts['subscription'],
        resource_group=master_parts['resource_group'],
        namespace='Microsoft.Network',
        type='virtualNetworks',
        name=master_parts['name'],
    )

    return get_network_resources(cli_ctx, worker_subnets | {master_subnet}, vnet)


def get_network_resources(cli_ctx, subnets, vnet):
    route_tables = get_route_tables_from_subnets(cli_ctx, subnets)

    resources = set()
    resources.add(vnet)
    resources.update(route_tables)

    return resources
