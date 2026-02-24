# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.command_modules.aro._actions import AROPlatformWorkloadIdentityAddAction
from azure.cli.command_modules.aro._validators import (
    validate_cidr,
    validate_client_id,
    validate_client_secret,
    validate_cluster_resource_group,
    validate_disk_encryption_set,
    validate_domain,
    validate_pull_secret,
    validate_subnet,
    validate_visibility,
    validate_vnet,
    validate_vnet_resource_group_name,
    validate_worker_count,
    validate_worker_vm_disk_size_gb,
    validate_refresh_cluster_credentials,
    validate_version_format,
    validate_outbound_type,
    validate_load_balancer_managed_outbound_ip_count,
    validate_enable_managed_identity,
    validate_platform_workload_identities,
    validate_cluster_identity,
    validate_cluster_identity_update,
    validate_delete_identities,
    validate_upgradeable_to_format,
)
from azure.cli.core.commands.parameters import (
    name_type,
    get_enum_type,
    get_three_state_flag,
    resource_group_name_type,
    tags_type
)
from azure.cli.core.commands.validators import get_default_location_from_resource_group


def load_arguments(self, _):
    with self.argument_context('aro') as c:
        c.argument('location',
                   validator=get_default_location_from_resource_group)
        c.argument('resource_name',
                   name_type,
                   help='Name of cluster.')
        c.argument('tags',
                   tags_type)

        c.argument('pull_secret',
                   help='Pull secret of cluster.',
                   validator=validate_pull_secret)
        c.argument('domain',
                   help='Domain of cluster.',
                   validator=validate_domain)
        c.argument('cluster_resource_group',
                   help='Resource group of cluster.',
                   validator=validate_cluster_resource_group)
        c.argument('fips_validated_modules', arg_type=get_three_state_flag(),
                   options_list=['--fips-validated-modules', '--fips'],
                   help='Use FIPS validated cryptography modules. [Default: false]')

        c.argument('client_id',
                   help='Client ID of cluster service principal.',
                   validator=validate_client_id(isCreate=True))
        c.argument('client_secret',
                   help='Client secret of cluster service principal.',
                   validator=validate_client_secret(isCreate=True))

        c.argument('version',
                   options_list=['--version', c.deprecate(target='--install-version', redirect='--version', hide=True)],
                   help='OpenShift version to use for cluster creation.',
                   validator=validate_version_format)

        c.argument('pod_cidr',
                   help='CIDR of pod network. Must be a minimum of /18 or larger. [Default: 10.128.0.0/14]',
                   validator=validate_cidr('pod_cidr'))
        c.argument('service_cidr',
                   help='CIDR of service network. Must be a minimum of /18 or larger. [Default: 172.30.0.0/16]',
                   validator=validate_cidr('service_cidr'))
        c.argument('outbound_type',
                   help='Outbound type of cluster. Must be "Loadbalancer" or "UserDefinedRouting". \
                   [Default: Loadbalancer]',
                   validator=validate_outbound_type)
        c.argument('enable_preconfigured_nsg', arg_type=get_three_state_flag(),
                   help='Use Preconfigured NSGs. Allowed values: false, true. [Default: false]')
        c.argument('disk_encryption_set',
                   help='ResourceID of the DiskEncryptionSet to be used for master and worker VMs.',
                   validator=validate_disk_encryption_set)
        c.argument('master_encryption_at_host', arg_type=get_three_state_flag(),
                   options_list=['--master-encryption-at-host', '--master-enc-host'],
                   help='Encryption at host flag for master VMs. [Default: false]')
        c.argument('master_vm_size',
                   help='Size of master VMs. [Default: Standard_D8s_v5]')

        c.argument('worker_encryption_at_host', arg_type=get_three_state_flag(),
                   options_list=['--worker-encryption-at-host', '--worker-enc-host'],
                   help='Encryption at host flag for worker VMs. [Default: false]')
        c.argument('worker_vm_size',
                   help='Size of worker VMs. [Default: Standard_D4s_v5]')
        c.argument('worker_vm_disk_size_gb',
                   type=int,
                   help='Disk size in GB of worker VMs. [Default: 128]',
                   validator=validate_worker_vm_disk_size_gb)
        c.argument('worker_count',
                   type=int,
                   help='Count of worker VMs. [Default: 3]',
                   validator=validate_worker_count)

        c.argument('apiserver_visibility', arg_type=get_enum_type(['Private', 'Public']),
                   help='API server visibility. [Default: Public]',
                   validator=validate_visibility('apiserver_visibility'))

        c.argument('ingress_visibility', arg_type=get_enum_type(['Private', 'Public']),
                   help='Ingress visibility. [Default: Public]',
                   validator=validate_visibility('ingress_visibility'))

        c.argument('vnet_resource_group_name',
                   resource_group_name_type,
                   options_list=['--vnet-resource-group'],
                   help='Name of vnet resource group.',
                   validator=validate_vnet_resource_group_name)
        c.argument('vnet',
                   help='Name or ID of vnet.  If name is supplied, `--vnet-resource-group` must be supplied.',
                   validator=validate_vnet)
        c.argument('master_subnet',
                   help='Name or ID of master vnet subnet.  If name is supplied, `--vnet` must be supplied.',
                   validator=validate_subnet('master_subnet'))
        c.argument('worker_subnet',
                   help='Name or ID of worker vnet subnet.  If name is supplied, `--vnet` must be supplied.',
                   validator=validate_subnet('worker_subnet'))
        c.argument('load_balancer_managed_outbound_ip_count',
                   type=int,
                   help='The desired number of IPv4 outbound IPs created and managed by Azure for the cluster public load balancer.',  # pylint: disable=line-too-long
                   validator=validate_load_balancer_managed_outbound_ip_count,
                   options_list=['--load-balancer-managed-outbound-ip-count', '--lb-ip-count'])

        c.argument('enable_managed_identity', arg_group='Identity', is_preview=True, arg_type=get_three_state_flag(),
                   help='Enable managed identity for this cluster.',
                   options_list=['--enable-managed-identity', '--enable-mi'],
                   validator=validate_enable_managed_identity)
        c.argument('platform_workload_identities', arg_group='Identity', is_preview=True,
                   help='Assign a platform workload identity used within the cluster. Requires two values: \
                           an operator name and either the name or resource ID of the Azure identity to use for it.',
                   options_list=['--assign-platform-workload-identity', '--assign-platform-wi'],
                   validator=validate_platform_workload_identities(isCreate=True),
                   action=AROPlatformWorkloadIdentityAddAction, nargs='+')
        c.argument('mi_user_assigned', arg_group='Identity', is_preview=True,
                   help='Set the user managed identity on the cluster. Value must be an identity name or resource ID.',
                   options_list=['--mi-user-assigned', '--assign-cluster-identity'],
                   validator=validate_cluster_identity)

    with self.argument_context('aro update') as c:
        c.argument('client_id',
                   help='Client ID of cluster service principal.',
                   validator=validate_client_id(isCreate=False))
        c.argument('client_secret',
                   help='Client secret of cluster service principal.',
                   validator=validate_client_secret(isCreate=False))
        c.argument('refresh_cluster_credentials',
                   arg_type=get_three_state_flag(),
                   help='Refresh cluster application credentials.',
                   options_list=['--refresh-credentials'],
                   validator=validate_refresh_cluster_credentials)
        c.argument('mi_user_assigned', arg_group='Identity', is_preview=True,
                   help='Set the user managed identity on the cluster. Value must be an identity name or resource ID.',
                   options_list=['--mi-user-assigned', '--assign-cluster-identity'],
                   validator=validate_cluster_identity_update)
        c.argument('platform_workload_identities', arg_group='Identity', is_preview=True,
                   help='Assign a platform workload identity used within the cluster. Requires two values: \
                           an operator name and either the name or resource ID of the Azure identity to use for it.',
                   options_list=['--assign-platform-workload-identity', '--assign-platform-wi'],
                   validator=validate_platform_workload_identities(isCreate=False),
                   action=AROPlatformWorkloadIdentityAddAction, nargs='+')
        c.argument('upgradeable_to', arg_group='Identity', options_list=['--upgradeable-to'],
                   help='OpenShift version to upgrade to.', is_preview=True,
                   validator=validate_upgradeable_to_format)

    with self.argument_context('aro get-admin-kubeconfig') as c:
        c.argument('file',
                   help='Path to the file where kubeconfig should be saved. Default: kubeconfig in local directory',
                   options_list=['--file', '-f'])

    with self.argument_context('aro delete') as c:
        c.argument('delete_identities',
                   is_preview=True,
                   arg_group='Identity',
                   arg_type=get_three_state_flag(),
                   validator=validate_delete_identities,
                   help='Delete the cluster\'s associated managed identities together with the cluster.')
