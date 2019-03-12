# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands.parameters import get_enum_type, name_type, tags_type, get_resource_name_completion_list, \
    get_generic_completion_list, get_three_state_flag
from ._validators import (validate_component_version,
                          validate_storage_account,
                          validate_msi,
                          validate_storage_msi,
                          validate_subnet,
                          validate_domain_service)

# Cluster types may be added in the future. Therefore, this list can be used for completion, but not input validation.
known_cluster_types = ["hadoop", "interactivehive", "hbase", "kafka", "storm", "spark", "rserver", "mlservices"]

# Known role (node) types.
known_role_types = ["headnode", "workernode", "zookeepernode", "edgenode"]


# pylint: disable=too-many-statements
def load_arguments(self, _):
    from ._completers import subnet_completion_list
    from knack.arguments import CLIArgumentType
    from azure.mgmt.hdinsight.models import Tier, JsonWebKeyEncryptionAlgorithm
    node_size_type = CLIArgumentType(arg_group='Node',
                                     help='The size of the node. See also: https://docs.microsoft.com/en-us/azure/'
                                          'hdinsight/hdinsight-hadoop-provision-linux-clusters#configure-cluster-size')

    # cluster
    with self.argument_context('hdinsight') as c:

        # Cluster
        c.argument('cluster_name', arg_type=name_type,
                   completer=get_resource_name_completion_list('Microsoft.HDInsight/clusters'),
                   help='The name of the cluster.')
        c.argument('tags', tags_type)
        c.argument('cluster_version', options_list=['--version', '-v'], arg_group='Cluster',
                   help='The HDInsight cluster version. See also: https://docs.microsoft.com/en-us/azure/'
                        'hdinsight/hdinsight-component-versioning#supported-hdinsight-versions')
        c.argument('cluster_type', options_list=['--type', '-t'], arg_group='Cluster',
                   completer=get_generic_completion_list(known_cluster_types),
                   help='Type of HDInsight cluster, like: {}. '
                        'See also: https://docs.microsoft.com/en-us/azure/hdinsight/hdinsight-'
                        'hadoop-provision-linux-clusters#cluster-types'.format(', '.join(known_cluster_types)))
        c.argument('component_version', arg_group='Cluster', nargs='*', validator=validate_component_version,
                   help='The versions of various Hadoop components, in space-'
                        'separated versions in \'component=version\' format. Example: '
                        'Spark=2.0 Hadoop=2.7.3 '
                        'See also: https://docs.microsoft.com/en-us/azure/hdinsight/hdinsight'
                        '-component-versioning#hadoop-components-available-with-different-'
                        'hdinsight-versions')
        c.argument('cluster_configurations', arg_group='Cluster',
                   help='Extra configurations of various components, in JSON.')
        c.argument('cluster_tier', arg_type=get_enum_type(Tier), arg_group='Cluster',
                   help='The tier of the cluster')
        c.argument('esp', arg_group='Cluster', arg_type=get_three_state_flag(),
                   help='Specify to create cluster with Enterprise Security Package')

        # HTTP
        c.argument('http_username', options_list=['--http-user', '-u'], arg_group='HTTP',
                   help='HTTP username for the cluster.  Default: admin.')
        c.argument('http_password', options_list=['--http-password', '-p'], arg_group='HTTP',
                   help='HTTP password for the cluster.')

        # SSH
        c.argument('ssh_username', options_list=['--ssh-user', '-U'], arg_group='SSH',
                   help='SSH username for the cluster nodes.')
        c.argument('ssh_password', options_list=['--ssh-password', '-P'], arg_group='SSH',
                   help='SSH password for the cluster nodes. If none specified, uses the HTTP password.')
        c.argument('ssh_public_key', options_list=['--ssh-public-key', '-K'], arg_group='SSH',
                   help='SSH public key for the cluster nodes.')

        # Node
        c.argument('headnode_size', arg_type=node_size_type)
        c.argument('workernode_size', arg_type=node_size_type)
        c.argument('workernode_data_disks_per_node', arg_group='Node',
                   help='The number of data disks to use per worker node.')
        c.argument('workernode_data_disk_storage_account_type', arg_group='Node',
                   arg_type=get_enum_type(['standard_lrs', 'premium_lrs']),
                   help='The type of storage account that will be used for the data disks: standard_lrs or premium_lrs')
        c.argument('workernode_data_disk_size', arg_group='Node',
                   help='The size of the data disk in GB, e.g. 1023.')
        c.argument('zookeepernode_size', arg_type=node_size_type)
        c.argument('edgenode_size', arg_type=node_size_type)
        c.argument('workernode_count', options_list=['--size', '-s'], arg_group='Node',
                   help='The number of worker nodes in the cluster.')

        # Storage
        c.argument('storage_account', arg_group='Storage', validator=validate_storage_account,
                   completer=get_resource_name_completion_list('Microsoft.Storage/storageAccounts'),
                   help='The name or ID of the storage account.')
        c.argument('storage_account_key', arg_group='Storage',
                   help='The storage account key. A key can be retrieved automatically '
                        'if the user has access to the storage account.')
        c.argument('storage_default_container', arg_group='Storage',
                   help='The storage container the cluster will use. '
                        'Uses the cluster name if none was specified. (WASB only)')
        c.argument('storage_default_filesystem', arg_group='Storage',
                   help='The storage filesystem the cluster will use. (DFS only)')
        c.argument('storage_account_managed_identity', arg_group='Storage', validator=validate_storage_msi,
                   completer=get_resource_name_completion_list('Microsoft.ManagedIdentity/userAssignedIdentities'),
                   help='User-assigned managed identity with access to the storage account filesystem. '
                        'Only required when storage account type is Azure Data Lake Storage Gen2.')

        # Network
        c.argument('vnet_name', arg_group='Network', validator=validate_subnet,
                   completer=get_resource_name_completion_list('Microsoft.Network/virtualNetworks'),
                   help='The name of a virtual network.')
        c.argument('subnet', arg_group='Network',
                   completer=subnet_completion_list,
                   help='The name or ID of subnet. If name is supplied, `--vnet-name` must be supplied.')

        # Script Action
        c.argument('script_action_name', arg_group='Script Action', help='The name of the script action.')
        c.argument('script_uri', arg_group='Script Action', help='The URI to the script.')
        c.argument('script_parameters', arg_group='Script Action', help='The parameters for the script.')

        # Domain Service
        c.argument('domain', arg_group='Domain Service', validator=validate_domain_service,
                   help='The name or resource ID of the user\'s Azure Active Directory Domain Service. '
                        'Required only when create cluster with Enterprise Security Package.')
        c.argument('cluster_users_group_dns', arg_group='Domain Service', nargs='+',
                   help='A space-delimited list of Distinguished Names for cluster user groups. '
                        'Required only when create cluster with Enterprise Security Package. ')
        c.argument('cluster_admin_password', arg_group='Domain Service',
                   help='The domain admin password. '
                        'Required only when create cluster with Enterprise Security Package.')
        c.argument('cluster_admin_account', arg_group='Domain Service',
                   help='The domain user account that will have admin privileges on the cluster. '
                        'Required only when create cluster with Enterprise Security Package.')
        c.argument('ldaps_urls', arg_group='Domain Service', nargs='+',
                   help='A space-delimited list of LDAPS protocol URLs to communicate with the Active Directory. '
                        'Required only when create cluster with Enterprise Security Package.')

        # Customer Managed Key
        c.argument('encryption_vault_uri', arg_group='Customer Managed Key',
                   help='Base key vault URI where the customers key is located eg. https://myvault.vault.azure.net')
        c.argument('encryption_key_name', arg_group='Customer Managed Key',
                   help='Key name that is used for enabling disk encryption.')
        c.argument('encryption_key_version', arg_group='Customer Managed Key',
                   help='Key version that is used for enabling disk encryption.')
        c.argument('encryption_algorithm', arg_type=get_enum_type(JsonWebKeyEncryptionAlgorithm),
                   arg_group='Customer Managed Key', help='Algorithm identifier for encryption.')

        # Managed Service Identity
        c.argument('assign_identity', arg_group='Managed Service Identity', validator=validate_msi,
                   help="The name or ID of user assigned identity.")

    # application
    with self.argument_context('hdinsight application') as c:
        c.argument('application_name', arg_group='Application', help='The constant value for the application name.')
        c.argument('application_type', arg_group='Application', help='The application type.')
        c.argument('marketplace_identifier', arg_group='Application', help='The marketplace identifier.')
        c.argument('https_endpoint_access_mode', arg_group='HTTPS Endpoint',
                   help='The access mode for the application.')
        c.argument('https_endpoint_destination_port', arg_group='HTTPS Endpoint',
                   help='The destination port to connect to.')
        c.argument('https_endpoint_location', arg_group='HTTPS Endpoint', help='The location of the endpoint.')
        c.argument('https_endpoint_public_port', arg_group='HTTPS Endpoint', help='The public port to connect to.')
        c.argument('ssh_endpoint_destination_port', arg_group='SSH Endpoint',
                   help='The destination port to connect to.')
        c.argument('ssh_endpoint_location', arg_group='SSH Endpoint', help='The location of the endpoint.')
        c.argument('ssh_endpoint_public_port', arg_group='SSH Endpoint', help='The public port to connect to.')
        c.argument('tags', tags_type)
        c.argument('ssh_password', options_list=['--ssh-password', '-P'], arg_group='SSH',
                   help='SSH password for the cluster nodes.')

    # script action
    with self.argument_context('hdinsight script-action') as c:
        c.argument('roles', arg_group='Script Action',
                   completer=get_generic_completion_list(known_role_types),
                   help='A comma-delimited list of roles (nodes) where the script will be executed. '
                        'Valid roles are {}.'.format(', '.join(known_role_types)))
        c.argument('persist_on_success', arg_group='Script Action', help='If the scripts needs to be persisted.')
        c.argument('persisted', arg_group='Script Action', help='If only list persisted script actions.')
        c.argument('script_name', options_list='--script-action-name', arg_group='Script Action',
                   help='The name of the script action.')

    # OMS
    with self.argument_context('hdinsight oms') as c:
        c.argument('workspace_id', arg_group='OMS', help='The Operations Management Suite (OMS) workspace ID.')
        c.argument('primary_key', arg_group='OMS', help='The Operations Management Suite (OMS) workspace key.')
