# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import random
import os

import azure.mgmt.redhatopenshift.models as v2020_04_30
from azure.cli.command_modules.aro._aad import AADManager
from azure.cli.command_modules.aro._rbac import assign_contributor_to_vnet, assign_contributor_to_routetable
from azure.cli.command_modules.aro._validators import validate_subnets
from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.core.commands.client_factory import get_subscription_id
from azure.cli.core.profiles import ResourceType
from azure.cli.core.util import sdk_no_wait
from knack.util import CLIError


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
        raise CLIError('Microsoft.RedHatOpenShift provider is not registered.  Run `az provider ' +
                       'register -n Microsoft.RedHatOpenShift --wait`.')

    vnet = validate_subnets(master_subnet, worker_subnet)

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

    for sp_id in [client_sp.object_id, rp_client_sp.object_id]:
        assign_contributor_to_vnet(cmd.cli_ctx, vnet, sp_id)
        assign_contributor_to_routetable(cmd.cli_ctx, master_subnet, worker_subnet, sp_id)

    if rp_mode_development():
        worker_vm_size = worker_vm_size or 'Standard_D2s_v3'
    else:
        worker_vm_size = worker_vm_size or 'Standard_D4s_v3'

    if apiserver_visibility is not None:
        apiserver_visibility = apiserver_visibility.capitalize()

    if ingress_visibility is not None:
        ingress_visibility = ingress_visibility.capitalize()

    oc = v2020_04_30.OpenShiftCluster(
        location=location,
        tags=tags,
        cluster_profile=v2020_04_30.ClusterProfile(
            pull_secret=pull_secret or "",
            domain=domain or random_id,
            resource_group_id='/subscriptions/%s/resourceGroups/%s' %
            (subscription_id, cluster_resource_group or "aro-" + random_id),
        ),
        service_principal_profile=v2020_04_30.ServicePrincipalProfile(
            client_id=client_id,
            client_secret=client_secret,
        ),
        network_profile=v2020_04_30.NetworkProfile(
            pod_cidr=pod_cidr or '10.128.0.0/14',
            service_cidr=service_cidr or '172.30.0.0/16',
        ),
        master_profile=v2020_04_30.MasterProfile(
            vm_size=master_vm_size or 'Standard_D8s_v3',
            subnet_id=master_subnet,
        ),
        worker_profiles=[
            v2020_04_30.WorkerProfile(
                name='worker',  # TODO: 'worker' should not be hard-coded
                vm_size=worker_vm_size,
                disk_size_gb=worker_vm_disk_size_gb or 128,
                subnet_id=worker_subnet,
                count=worker_count or 3,
            )
        ],
        apiserver_profile=v2020_04_30.APIServerProfile(
            visibility=apiserver_visibility or 'Public',
        ),
        ingress_profiles=[
            v2020_04_30.IngressProfile(
                name='default',  # TODO: 'default' should not be hard-coded
                visibility=ingress_visibility or 'Public',
            )
        ],
    )

    return sdk_no_wait(no_wait, client.create_or_update,
                       resource_group_name=resource_group_name,
                       resource_name=resource_name,
                       parameters=oc)


def aro_delete(client, resource_group_name, resource_name, no_wait=False):
    # TODO: clean up rbac

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


def aro_update(client, resource_group_name, resource_name, no_wait=False):
    oc = v2020_04_30.OpenShiftClusterUpdate()

    return sdk_no_wait(no_wait, client.update,
                       resource_group_name=resource_group_name,
                       resource_name=resource_name,
                       parameters=oc)


def rp_mode_development():
    return os.environ.get('RP_MODE', '').lower() == 'development'


def generate_random_id():
    random_id = (random.choice('abcdefghijklmnopqrstuvwxyz') +
                 ''.join(random.choice('abcdefghijklmnopqrstuvwxyz1234567890')
                         for _ in range(7)))
    return random_id
