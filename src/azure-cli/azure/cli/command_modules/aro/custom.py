# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import collections
import random
from base64 import b64decode
import textwrap

from azure.core.exceptions import HttpResponseError, \
    ResourceNotFoundError as CoreResourceNotFoundError
from azure.mgmt.core.tools import resource_id, parse_resource_id
import azure.mgmt.redhatopenshift.models as openshiftcluster

from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.core.commands.client_factory import get_subscription_id
from azure.cli.core.profiles import ResourceType
from azure.cli.core.util import sdk_no_wait
from azure.cli.core.azclierror import FileOperationError, ResourceNotFoundError, \
    UnauthorizedError, ValidationError
from azure.cli.command_modules.aro._aad import AADManager
from azure.cli.command_modules.aro._rbac import assign_role_to_resource, \
    has_role_assignment_on_resource
from azure.cli.command_modules.aro._rbac import ROLE_NETWORK_CONTRIBUTOR, ROLE_READER
from azure.cli.command_modules.aro._validators import validate_subnets
from azure.cli.command_modules.aro._dynamic_validators import validate_cluster_create
from azure.cli.command_modules.aro.aaz.latest.network.vnet.subnet import Show as subnet_show
from azure.cli.command_modules.role import GraphError

from knack.log import get_logger

from msrest.exceptions import HttpOperationError

from tabulate import tabulate

logger = get_logger(__name__)

FP_CLIENT_ID = 'f1dd0a37-89c6-4e07-bcd1-ffd3d43d8875'


def aro_create(cmd,  # pylint: disable=too-many-locals
               client,
               resource_group_name,
               resource_name,
               master_subnet,
               worker_subnet,
               vnet=None,  # pylint: disable=unused-argument
               vnet_resource_group_name=None,  # pylint: disable=unused-argument
               enable_preconfigured_nsg=False,
               location=None,
               pull_secret=None,
               domain=None,
               cluster_resource_group=None,
               fips_validated_modules=False,
               client_id=None,
               client_secret=None,
               pod_cidr='10.128.0.0/14',
               service_cidr='172.30.0.0/16',
               outbound_type='Loadbalancer',
               disk_encryption_set=None,
               master_encryption_at_host=False,
               master_vm_size='Standard_D8s_v5',
               worker_encryption_at_host=False,
               worker_vm_size='Standard_D4s_v5',
               worker_vm_disk_size_gb='128',
               worker_count='3',
               apiserver_visibility='Public',
               ingress_visibility='Public',
               load_balancer_managed_outbound_ip_count=None,
               tags=None,
               version=None,
               no_wait=False):

    resource_client = get_mgmt_service_client(
        cmd.cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES)
    provider = resource_client.providers.get('Microsoft.RedHatOpenShift')
    if provider.registration_state != 'Registered':
        raise UnauthorizedError('Microsoft.RedHatOpenShift provider is not registered.',
                                'Run `az provider register -n Microsoft.RedHatOpenShift --wait`.')

    validate_subnets(master_subnet, worker_subnet)

    validate(cmd,
             client,
             resource_group_name,
             resource_name,
             master_subnet,
             worker_subnet,
             vnet=vnet,
             enable_preconfigured_nsg=enable_preconfigured_nsg,
             cluster_resource_group=cluster_resource_group,
             client_id=client_id,
             client_secret=client_secret,
             vnet_resource_group_name=vnet_resource_group_name,
             disk_encryption_set=disk_encryption_set,
             location=location,
             version=version,
             pod_cidr=pod_cidr,
             service_cidr=service_cidr,
             warnings_as_text=True)

    subscription_id = get_subscription_id(cmd.cli_ctx)

    random_id = generate_random_id()

    aad = AADManager(cmd.cli_ctx)
    if client_id is None:
        client_id, client_secret = aad.create_application(cluster_resource_group or 'aro-' + random_id)

    client_sp_id = aad.get_service_principal_id(client_id)
    if not client_sp_id:
        client_sp_id = aad.create_service_principal(client_id)

    rp_client_sp_id = aad.get_service_principal_id(resolve_rp_client_id())
    if not rp_client_sp_id:
        raise ResourceNotFoundError("RP service principal not found.")

    worker_vm_size = worker_vm_size or 'Standard_D4s_v5'

    if apiserver_visibility is not None:
        apiserver_visibility = apiserver_visibility.capitalize()

    if ingress_visibility is not None:
        ingress_visibility = ingress_visibility.capitalize()

    load_balancer_profile = None
    if load_balancer_managed_outbound_ip_count is not None:
        load_balancer_profile = openshiftcluster.LoadBalancerProfile()
        load_balancer_profile.managed_outbound_ips = openshiftcluster.ManagedOutboundIPs()
        load_balancer_profile.managed_outbound_ips.count = load_balancer_managed_outbound_ip_count  # pylint: disable=line-too-long

    oc = openshiftcluster.OpenShiftCluster(
        location=location,
        tags=tags,
        cluster_profile=openshiftcluster.ClusterProfile(
            pull_secret=pull_secret or "",
            domain=domain or random_id,
            resource_group_id=(f"/subscriptions/{subscription_id}"
                               f"/resourceGroups/{cluster_resource_group or 'aro-' + random_id}"),
            fips_validated_modules='Enabled' if fips_validated_modules else 'Disabled',
            version=version or '',
        ),
        service_principal_profile=openshiftcluster.ServicePrincipalProfile(
            client_id=client_id,
            client_secret=client_secret,
        ),
        network_profile=openshiftcluster.NetworkProfile(
            pod_cidr=pod_cidr or '10.128.0.0/14',
            service_cidr=service_cidr or '172.30.0.0/16',
            outbound_type=outbound_type or '',
            load_balancer_profile=load_balancer_profile,
            preconfigured_nsg='Enabled' if enable_preconfigured_nsg else 'Disabled',
        ),
        master_profile=openshiftcluster.MasterProfile(
            vm_size=master_vm_size or 'Standard_D8s_v5',
            subnet_id=master_subnet,
            encryption_at_host='Enabled' if master_encryption_at_host else 'Disabled',
            disk_encryption_set_id=disk_encryption_set,
        ),
        worker_profiles=[
            openshiftcluster.WorkerProfile(
                name='worker',  # TODO: 'worker' should not be hard-coded
                vm_size=worker_vm_size,
                disk_size_gb=worker_vm_disk_size_gb or 128,
                subnet_id=worker_subnet,
                count=worker_count or 3,
                encryption_at_host='Enabled' if worker_encryption_at_host else 'Disabled',
                disk_encryption_set_id=disk_encryption_set,
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

    sp_obj_ids = [client_sp_id, rp_client_sp_id]
    ensure_resource_permissions(cmd.cli_ctx, oc, True, sp_obj_ids)

    return sdk_no_wait(no_wait, client.open_shift_clusters.begin_create_or_update,
                       resource_group_name=resource_group_name,
                       resource_name=resource_name,
                       parameters=oc)


def validate(cmd,  # pylint: disable=too-many-locals,too-many-statements
             client,  # pylint: disable=unused-argument
             resource_group_name,  # pylint: disable=unused-argument
             resource_name,  # pylint: disable=unused-argument
             master_subnet,
             worker_subnet,
             vnet=None,
             enable_preconfigured_nsg=None,
             cluster_resource_group=None,  # pylint: disable=unused-argument
             client_id=None,
             client_secret=None,  # pylint: disable=unused-argument
             vnet_resource_group_name=None,  # pylint: disable=unused-argument
             disk_encryption_set=None,
             location=None,  # pylint: disable=unused-argument
             version=None,
             pod_cidr=None,  # pylint: disable=unused-argument
             service_cidr=None,  # pylint: disable=unused-argument
             warnings_as_text=False):

    class mockoc:  # pylint: disable=too-few-public-methods
        def __init__(self, disk_encryption_id, master_subnet_id, worker_subnet_id, preconfigured_nsg):
            self.network_profile = openshiftcluster.NetworkProfile(
                preconfigured_nsg='Enabled' if preconfigured_nsg else 'Disabled'
            )
            self.master_profile = openshiftcluster.MasterProfile(
                subnet_id=master_subnet_id,
                disk_encryption_set_id=disk_encryption_id
            )
            self.worker_profiles = [openshiftcluster.WorkerProfile(
                subnet_id=worker_subnet_id
            )]
            self.worker_profiles_status = None

    aad = AADManager(cmd.cli_ctx)

    rp_client_sp_id = aad.get_service_principal_id(resolve_rp_client_id())
    if not rp_client_sp_id:
        raise ResourceNotFoundError("RP service principal not found.")

    sp_obj_ids = [rp_client_sp_id]

    if client_id is not None:
        sp_obj_ids.append(aad.get_service_principal_id(client_id))

    cluster = mockoc(disk_encryption_set, master_subnet, worker_subnet, enable_preconfigured_nsg)
    try:
        # Get cluster resources we need to assign permissions on, sort to ensure the same order of operations
        resources = {ROLE_NETWORK_CONTRIBUTOR: sorted(get_cluster_network_resources(cmd.cli_ctx, cluster, True)),
                     ROLE_READER: sorted(get_disk_encryption_resources(cluster))}
    except (HttpResponseError, HttpOperationError) as e:
        logger.error(e.message)
        raise

    if vnet is None:
        master_parts = parse_resource_id(master_subnet)
        vnet = resource_id(
            subscription=master_parts['subscription'],
            resource_group=master_parts['resource_group'],
            namespace='Microsoft.Network',
            type='virtualNetworks',
            name=master_parts['name'],
        )

    error_objects = validate_cluster_create(version,
                                            resources,
                                            sp_obj_ids)
    errors_and_warnings = []
    for error_func in error_objects:
        namespace = collections.namedtuple("Namespace", locals().keys())(*locals().values())
        error_obj = error_func(cmd, namespace)
        if error_obj != []:
            for err in error_obj:
                # Wrap text so tabulate returns a pretty table
                new_err = []
                for txt in err:
                    new_err.append(textwrap.fill(txt, width=160))
                errors_and_warnings.append(new_err)

    warnings = []
    errors = []
    if len(errors_and_warnings) > 0:
        # Separate errors and warnings into separate arrays
        for issue in errors_and_warnings:
            if issue[2] == "Warning":
                warnings.append(issue)
            else:
                errors.append(issue)
    else:
        logger.info("No validation errors or warnings")

    if len(warnings) > 0:
        if len(errors) == 0 and warnings_as_text:
            full_msg = ""
            for warning in warnings:
                full_msg = full_msg + f"{warning[3]}\n"
        else:
            headers = ["Type", "Name", "Severity", "Description"]
            table = tabulate(warnings, headers=headers, tablefmt="grid")
            full_msg = f"The following issues will have a minor impact on cluster creation:\n{table}"
        logger.warning(full_msg)

    if len(errors) > 0:
        if len(warnings) > 0:
            full_msg = "\n"
        else:
            full_msg = ""
        headers = ["Type", "Name", "Severity", "Description"]
        table = tabulate(errors, headers=headers, tablefmt="grid")
        full_msg = full_msg + f"The following errors are fatal and will block cluster creation:\n{table}"
        raise ValidationError(full_msg)


def aro_validate(cmd,  # pylint: disable=too-many-locals,too-many-statements
                 client,  # pylint: disable=unused-argument
                 resource_group_name,  # pylint: disable=unused-argument
                 resource_name,  # pylint: disable=unused-argument
                 master_subnet,
                 worker_subnet,
                 vnet=None,
                 cluster_resource_group=None,  # pylint: disable=unused-argument
                 client_id=None,
                 client_secret=None,  # pylint: disable=unused-argument
                 vnet_resource_group_name=None,  # pylint: disable=unused-argument
                 disk_encryption_set=None,
                 location=None,  # pylint: disable=unused-argument
                 version=None,
                 pod_cidr=None,  # pylint: disable=unused-argument
                 service_cidr=None,  # pylint: disable=unused-argument
                 ):

    validate(cmd,
             client,
             resource_group_name,
             resource_name,
             master_subnet,
             worker_subnet,
             vnet=vnet,
             cluster_resource_group=cluster_resource_group,
             client_id=client_id,
             client_secret=client_secret,
             vnet_resource_group_name=vnet_resource_group_name,
             disk_encryption_set=disk_encryption_set,
             location=location,
             version=version,
             pod_cidr=pod_cidr,
             service_cidr=service_cidr,
             warnings_as_text=False)


def aro_delete(cmd, client, resource_group_name, resource_name, no_wait=False):
    # TODO: clean up rbac
    rp_client_sp_id = None

    try:
        oc = client.open_shift_clusters.get(resource_group_name, resource_name)
    except HttpResponseError as e:
        if e.status_code == 404:
            raise ResourceNotFoundError(e.message) from e
        logger.info(e.message)
    except HttpOperationError as e:
        logger.info(e.message)

    aad = AADManager(cmd.cli_ctx)

    # Best effort - assume the role assignments on the SP exist if exception raised
    try:
        rp_client_sp_id = aad.get_service_principal_id(resolve_rp_client_id())
        if not rp_client_sp_id:
            raise ResourceNotFoundError("RP service principal not found.")
    except GraphError as e:
        logger.info(e)

    # Customers frequently remove the Cluster or RP's service principal permissions.
    # Attempt to fix this before performing any action against the cluster
    if rp_client_sp_id:
        ensure_resource_permissions(cmd.cli_ctx, oc, False, [rp_client_sp_id])

    return sdk_no_wait(no_wait, client.open_shift_clusters.begin_delete,
                       resource_group_name=resource_group_name,
                       resource_name=resource_name)


def aro_list(client, resource_group_name=None):
    if resource_group_name:
        return client.open_shift_clusters.list_by_resource_group(resource_group_name)
    return client.open_shift_clusters.list()


def aro_show(client, resource_group_name, resource_name):
    return client.open_shift_clusters.get(resource_group_name, resource_name)


def aro_list_credentials(client, resource_group_name, resource_name):
    return client.open_shift_clusters.list_credentials(resource_group_name, resource_name)


def aro_get_admin_kubeconfig(client, resource_group_name, resource_name, file="kubeconfig"):
    query_result = client.open_shift_clusters.list_admin_credentials(resource_group_name, resource_name)
    file_mode = "x"
    yaml_data = b64decode(query_result.kubeconfig).decode('UTF-8')
    try:
        with open(file, file_mode, encoding="utf-8") as f:
            f.write(yaml_data)
    except FileExistsError as e:
        raise FileOperationError(f"File {file} already exists.") from e
    logger.info("Kubeconfig written to file: %s", file)


def aro_get_versions(client, location):
    items = client.open_shift_versions.list(location)
    versions = []
    for item in items:
        versions.append(item.version)
    return sorted(versions)


def aro_update(cmd,
               client,
               resource_group_name,
               resource_name,
               refresh_cluster_credentials=False,
               client_id=None,
               client_secret=None,
               load_balancer_managed_outbound_ip_count=None,
               no_wait=False):
    # if we can't read cluster spec, we will not be able to do much. Fail.
    oc = client.open_shift_clusters.get(resource_group_name, resource_name)

    ocUpdate = openshiftcluster.OpenShiftClusterUpdate()

    client_id, client_secret = cluster_application_update(cmd.cli_ctx, oc, client_id, client_secret, refresh_cluster_credentials)  # pylint: disable=line-too-long

    if client_id is not None or client_secret is not None:
        # construct update payload
        ocUpdate.service_principal_profile = openshiftcluster.ServicePrincipalProfile()

        if client_secret is not None:
            ocUpdate.service_principal_profile.client_secret = client_secret

        if client_id is not None:
            ocUpdate.service_principal_profile.client_id = client_id

    if load_balancer_managed_outbound_ip_count is not None:
        ocUpdate.network_profile = openshiftcluster.NetworkProfile()
        ocUpdate.network_profile.load_balancer_profile = openshiftcluster.LoadBalancerProfile()
        ocUpdate.network_profile.load_balancer_profile.managed_outbound_ips = openshiftcluster.ManagedOutboundIPs()
        ocUpdate.network_profile.load_balancer_profile.managed_outbound_ips.count = load_balancer_managed_outbound_ip_count  # pylint: disable=line-too-long

    return sdk_no_wait(no_wait, client.open_shift_clusters.begin_update,
                       resource_group_name=resource_group_name,
                       resource_name=resource_name,
                       parameters=ocUpdate)


def generate_random_id():
    random_id = (random.choice('abcdefghijklmnopqrstuvwxyz') +
                 ''.join(random.choice('abcdefghijklmnopqrstuvwxyz1234567890')
                         for _ in range(7)))
    return random_id


def get_network_resources_from_subnets(cli_ctx, subnets, fail, oc):

    subnet_resources = set()
    subnets_with_no_nsg_attached = set()
    for sn in subnets:
        sid = parse_resource_id(sn)

        if 'resource_group' not in sid or 'name' not in sid or 'resource_name' not in sid:
            if fail:
                raise ValidationError(f"""(ValidationError) Failed to validate subnet '{sn}'.
                    Please retry, if issue persists: raise azure support ticket""")
            logger.info("Failed to validate subnet '%s'", sn)

        try:
            subnet = subnet_show(cli_ctx=cli_ctx)(command_args={
                "name": sid['resource_name'],
                "vnet_name": sid['name'],
                "resource_group": sid['resource_group']}
            )
        except CoreResourceNotFoundError:
            continue

        if subnet.get("routeTable", None):
            subnet_resources.add(subnet["routeTable"]["id"])

        if subnet.get("natGateway", None):
            subnet_resources.add(subnet["natGateway"]["id"])

        if oc.network_profile.preconfigured_nsg == 'Enabled':
            if subnet.get("networkSecurityGroup", None):
                subnet_resources.add(subnet['networkSecurityGroup']['id'])
            else:
                subnets_with_no_nsg_attached.add(sn)

    # when preconfiguredNSG feature is Enabled we either have all subnets NSG attached or none.
    if oc.network_profile.preconfigured_nsg == 'Enabled' and \
        len(subnets_with_no_nsg_attached) != 0 and \
            len(subnets_with_no_nsg_attached) != len(subnets):
        raise ValidationError(f"(ValidationError) preconfiguredNSG feature is enabled but an NSG is\
                               not attached for all required subnets. Please make sure all the following\
                               subnets have a network security groups attached and retry.\
                              {subnets_with_no_nsg_attached}")

    return subnet_resources


def get_cluster_network_resources(cli_ctx, oc, fail):
    master_subnet = oc.master_profile.subnet_id
    worker_subnets = set()

    # Ensure that worker_profiles exists
    # it will not be returned if the cluster resources do not exist
    if oc.worker_profiles is not None:
        worker_subnets = {w.subnet_id for w in oc.worker_profiles}

    # Ensure that worker_profiles_status exists
    # it will not be returned if the cluster resources do not exist

    # We filter nonexistent subnets here as we only propagate subnet values for
    # worker profiles/machinesets considered valid.
    if oc.worker_profiles_status is not None:
        worker_subnets |= {w.subnet_id for w in oc.worker_profiles_status if w.subnet_id is not None}

    master_parts = parse_resource_id(master_subnet)
    vnet = resource_id(
        subscription=master_parts['subscription'],
        resource_group=master_parts['resource_group'],
        namespace='Microsoft.Network',
        type='virtualNetworks',
        name=master_parts['name'],
    )

    return get_network_resources(cli_ctx, worker_subnets | {master_subnet}, vnet, fail, oc)


def get_network_resources(cli_ctx, subnets, vnet, fail, oc):
    subnet_resources = get_network_resources_from_subnets(cli_ctx, subnets, fail, oc)

    resources = set()
    resources.add(vnet)
    resources.update(subnet_resources)

    return resources


def get_disk_encryption_resources(oc):
    disk_encryption_set = oc.master_profile.disk_encryption_set_id
    resources = set()
    if disk_encryption_set:
        resources.add(disk_encryption_set)
    return resources


# cluster_application_update manages cluster application & service principal update
# If called without parameters it should be best-effort
# If called with parameters it fails if something is not possible
# Flow:
# 1. Set fail - if we are in fail mode or best effort.
# 2. Sort out client_id, rp_client_sp, resources we care for RBAC.
# 3. If we are in refresh_cluster_credentials mode - attempt to reuse/recreate
# cluster service principal application and acquire client_id, client_secret
# 4. Reuse/Recreate service principal.
# 5. Sort out required rbac
def cluster_application_update(cli_ctx,
                               oc,
                               client_id,
                               client_secret,
                               refresh_cluster_credentials):
    # QUESTION: is there possible unification with the create path?

    rp_client_sp_id = None
    client_sp_id = None
    random_id = generate_random_id()

    # if any of these are set - we expect users to have access to fix rbac so we fail
    # common for 1 and 2 flows
    fail = client_id or client_secret or refresh_cluster_credentials

    aad = AADManager(cli_ctx)

    # check if we can see if RP service principal exists
    try:
        rp_client_sp_id = aad.get_service_principal_id(resolve_rp_client_id())
        if not rp_client_sp_id:
            raise ResourceNotFoundError("RP service principal not found.")
    except GraphError as e:
        if fail:
            logger.error(e)
            raise
        logger.info(e)

    # refresh_cluster_credentials refreshes cluster SP application.
    # At firsts it tries to re-use existing application and generate new password.
    # If application does not exist - creates new one
    if refresh_cluster_credentials:
        try:
            app = aad.get_application_object_id_by_client_id(client_id or oc.service_principal_profile.client_id)
            if not app:
                # we were not able to find and applications, create new one
                parts = parse_resource_id(oc.cluster_profile.resource_group_id)
                cluster_resource_group = parts['resource_group']

                client_id, client_secret = aad.create_application(cluster_resource_group or 'aro-' + random_id)
            else:
                client_secret = aad.add_password(app)
        except GraphError as e:
            logger.error(e)
            raise

    # attempt to get/create SP if one was not found.
    try:
        client_sp_id = aad.get_service_principal_id(client_id or oc.service_principal_profile.client_id)
    except GraphError as e:
        if fail:
            logger.error(e)
            raise
        logger.info(e)

    if fail and not client_sp_id:
        client_sp_id = aad.create_service_principal(client_id or oc.service_principal_profile.client_id)

    sp_obj_ids = [sp for sp in [rp_client_sp_id, client_sp_id] if sp]
    ensure_resource_permissions(cli_ctx, oc, fail, sp_obj_ids)

    return client_id, client_secret


def resolve_rp_client_id():
    return FP_CLIENT_ID


def ensure_resource_permissions(cli_ctx, oc, fail, sp_obj_ids):
    try:
        # Get cluster resources we need to assign permissions on, sort to ensure the same order of operations
        resources = {ROLE_NETWORK_CONTRIBUTOR: sorted(get_cluster_network_resources(cli_ctx, oc, fail)),
                     ROLE_READER: sorted(get_disk_encryption_resources(oc))}
    except (HttpResponseError, HttpOperationError) as e:
        if fail:
            logger.error(e.message)
            raise
        logger.info(e.message)
        return

    for sp_id in sp_obj_ids:
        for role in sorted(resources):
            for resource in resources[role]:
                # Create the role assignment if it doesn't exist
                # Assume that the role assignment exists if we fail to look it up
                resource_contributor_exists = True
                try:
                    resource_contributor_exists = has_role_assignment_on_resource(cli_ctx, resource, sp_id, role)
                except HttpResponseError as e:
                    if fail:
                        logger.error(e.message)
                        raise
                    logger.info(e.message)

                if not resource_contributor_exists:
                    assign_role_to_resource(cli_ctx, resource, sp_id, role)
