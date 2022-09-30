# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands.parameters import get_enum_type, name_type, tags_type, \
    get_generic_completion_list, get_three_state_flag, get_resource_name_completion_list
from azure.cli.core.util import shell_safe_json_parse
from ._validators import (validate_component_version,
                          validate_storage_account,
                          validate_msi,
                          validate_storage_msi,
                          validate_subnet,
                          validate_domain_service,
                          validate_workspace,
                          validate_timezone_name, validate_time)
from .util import AUTOSCALE_TIMEZONES

# Cluster types may be added in the future. Therefore, this list can be used for completion, but not input validation.
known_cluster_types = ["hadoop", "interactivehive", "hbase", "kafka", "storm", "spark", "rserver", "mlservices"]

# Known role (node) types.
known_role_types = ["headnode", "workernode", "zookeepernode", "edgenode"]
week_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
known_autoscale_types = ["Load", "Schedule"]


# pylint: disable=too-many-statements
def load_arguments(self, _):
    from ._completers import subnet_completion_list, cluster_admin_account_completion_list, \
        cluster_user_group_completion_list, get_resource_name_completion_list_under_subscription
    from knack.arguments import CLIArgumentType
    from azure.mgmt.hdinsight.models import Tier, JsonWebKeyEncryptionAlgorithm, ResourceProviderConnection
    from argcomplete.completers import FilesCompleter
    node_size_type = CLIArgumentType(arg_group='Node',
                                     help='The size of the node. See also: https://docs.microsoft.com/azure/'
                                          'hdinsight/hdinsight-hadoop-provision-linux-clusters#configure-cluster-size')

    # cluster
    with self.argument_context('hdinsight') as c:
        # Cluster
        c.argument('cluster_name', arg_type=name_type,
                   completer=get_resource_name_completion_list('Microsoft.HDInsight/clusters'),
                   help='The name of the cluster.')
        c.argument('tags', tags_type)
        c.argument('no_validation_timeout', action='store_true',
                   help='Permit timeout error during argument validation phase. If omitted, '
                        'validation timeout error will be permitted.')
        c.argument('cluster_version', options_list=['--version', '-v'], arg_group='Cluster',
                   help='The HDInsight cluster version. See also: https://docs.microsoft.com/azure/'
                        'hdinsight/hdinsight-component-versioning#supported-hdinsight-versions')
        c.argument('cluster_type', options_list=['--type', '-t'], arg_group='Cluster',
                   completer=get_generic_completion_list(known_cluster_types),
                   help='Type of HDInsight cluster, like: {}. '
                        'See also: https://docs.microsoft.com/azure/hdinsight/hdinsight-'
                        'hadoop-provision-linux-clusters#cluster-types'.format(', '.join(known_cluster_types)))
        c.argument('component_version', arg_group='Cluster', nargs='*', validator=validate_component_version,
                   help='The versions of various Hadoop components, in space-'
                        'separated versions in \'component=version\' format. Example: '
                        'Spark=2.0 Hadoop=2.7.3 '
                        'See also: https://docs.microsoft.com/azure/hdinsight/hdinsight'
                        '-component-versioning#hadoop-components-available-with-different-'
                        'hdinsight-versions')
        c.argument('cluster_configurations', arg_group='Cluster', type=shell_safe_json_parse,
                   completer=FilesCompleter(),
                   help='Extra configurations of various components. '
                        'Configurations may be supplied from a file using the `@{path}` syntax or a JSON string. '
                        'See also: https://docs.microsoft.com/azure/hdinsight/'
                        'hdinsight-hadoop-customize-cluster-bootstrap')
        c.argument('cluster_tier', arg_type=get_enum_type(Tier), arg_group='Cluster',
                   help='The tier of the cluster')
        c.argument('esp', arg_group='Cluster', action='store_true',
                   help='Specify to create cluster with Enterprise Security Package. If omitted, '
                        'creating cluster with Enterprise Security Package will not not allowed.')
        c.argument('idbroker', arg_group='Cluster', action='store_true',
                   help='Specify to create ESP cluster with HDInsight ID Broker. If omitted, '
                        'creating ESP cluster with HDInsight ID Broker will not not allowed.')
        c.argument('minimal_tls_version', arg_type=get_enum_type(['1.0', '1.1', '1.2']),
                   arg_group='Cluster', help='The minimal supported TLS version.')

        # HTTP
        c.argument('http_username', options_list=['--http-user', '-u'], arg_group='HTTP',
                   help='HTTP username for the cluster.  Default: admin.')
        c.argument('http_password', options_list=['--http-password', '-p'], arg_group='HTTP',
                   help='HTTP password for the cluster. Will prompt if not given.')

        # SSH
        c.argument('ssh_username', options_list=['--ssh-user', '-U'], arg_group='SSH',
                   help='SSH username for the cluster nodes.')
        c.argument('ssh_password', options_list=['--ssh-password', '-P'], arg_group='SSH',
                   help='SSH password for the cluster nodes. If none specified, uses the HTTP password.')
        c.argument('ssh_public_key', options_list=['--ssh-public-key', '-K'], arg_group='SSH',
                   help='SSH public key for the cluster nodes.')

        # Node
        c.argument('headnode_size', arg_type=node_size_type,
                   help='The size of the node. See also: https://docs.microsoft.com/azure/'
                        'hdinsight/hdinsight-hadoop-provision-linux-clusters#configure-cluster-size')
        c.argument('workernode_size', arg_type=node_size_type,
                   help='The size of the node. See also: https://docs.microsoft.com/azure/'
                        'hdinsight/hdinsight-hadoop-provision-linux-clusters#configure-cluster-size')
        c.argument('workernode_data_disks_per_node', arg_group='Node',
                   help='The number of data disks to use per worker node.')
        c.argument('workernode_data_disk_storage_account_type', arg_group='Node',
                   arg_type=get_enum_type(['standard_lrs', 'premium_lrs']),
                   help='The type of storage account that will be used for the data disks: standard_lrs or premium_lrs')
        c.argument('workernode_data_disk_size', arg_group='Node',
                   help='The size of the data disk in GB, e.g. 1023.')
        c.argument('zookeepernode_size', arg_type=node_size_type)
        c.argument('edgenode_size', arg_type=node_size_type)
        c.argument('kafka_management_node_size', arg_type=node_size_type)
        c.argument('workernode_count', options_list=['--workernode-count', '-c'], arg_group='Node',
                   help='The number of worker nodes in the cluster.')
        c.argument('kafka_management_node_count', arg_group='Node',
                   help='The number of kafka management node in the cluster')

        # Storage
        c.argument('storage_account', arg_group='Storage', validator=validate_storage_account,
                   completer=get_resource_name_completion_list_under_subscription('Microsoft.Storage/storageAccounts'),
                   help='The name or ID of the storage account.')
        c.argument('storage_account_key', arg_group='Storage',
                   help='The storage account key. A key can be retrieved automatically '
                        'if the user has access to the storage account.')
        c.argument('storage_default_container', arg_group='Storage', options_list=['--storage-container'],
                   help='The storage container the cluster will use. '
                        'Uses the cluster name if none was specified. (WASB only)')
        c.argument('storage_default_filesystem', arg_group='Storage', options_list=['--storage-filesystem'],
                   help='The storage filesystem the cluster will use. '
                        'Uses the cluster name if none was specified. (DFS only)')
        c.argument('storage_account_managed_identity', arg_group='Storage', validator=validate_storage_msi,
                   completer=get_resource_name_completion_list_under_subscription(
                       'Microsoft.ManagedIdentity/userAssignedIdentities'),
                   help='User-assigned managed identity with access to the storage account filesystem. '
                        'Only required when storage account type is Azure Data Lake Storage Gen2.')

        # Network
        c.argument('vnet_name', arg_group='Network', validator=validate_subnet,
                   completer=get_resource_name_completion_list_under_subscription('Microsoft.Network/virtualNetworks'),
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
                   completer=get_resource_name_completion_list_under_subscription('Microsoft.AAD/domainServices'),
                   help='The name or resource ID of the user\'s Azure Active Directory Domain Service. '
                        'Required only when create cluster with Enterprise Security Package.')
        c.argument('cluster_users_group_dns', arg_group='Domain Service', nargs='+',
                   completer=cluster_user_group_completion_list,
                   help='A space-delimited list of Distinguished Names for cluster user groups. '
                        'Required only when create cluster with Enterprise Security Package. ')
        c.argument('cluster_admin_password', arg_group='Domain Service',
                   help='The domain admin password. '
                        'Required only when create cluster with Enterprise Security Package.')
        c.argument('cluster_admin_account', arg_group='Domain Service',
                   completer=cluster_admin_account_completion_list,
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

        # Kafka Rest Proxy
        c.argument('kafka_client_group_id', arg_group='Kafka Rest Proxy',
                   help='The client AAD security group id for Kafka Rest Proxy')
        c.argument('kafka_client_group_name', arg_group='Kafka Rest Proxy',
                   help='The client AAD security group name for Kafka Rest Proxy')

        # Managed Service Identity
        c.argument('assign_identity', arg_group='Managed Service Identity', validator=validate_msi,
                   completer=get_resource_name_completion_list_under_subscription(
                       'Microsoft.ManagedIdentity/userAssignedIdentities'),
                   help="The name or ID of user assigned identity.")

        # Encryption In Transit
        c.argument('encryption_in_transit', arg_group='Encryption In Transit', arg_type=get_three_state_flag(),
                   help='Indicates whether enable encryption in transit.')

        # Encryption At Host
        c.argument('encryption_at_host', arg_group='Encryption At Host', arg_type=get_three_state_flag(),
                   help='Indicates whether enable encryption at host or not.')

        # Autoscale Configuration
        c.argument('autoscale_type', arg_group='Autoscale Configuration', arg_type=get_enum_type(known_autoscale_types),
                   help='The autoscale type.')
        c.argument('autoscale_min_workernode_count', type=int,
                   options_list=['--autoscale-min-workernode-count', '--autoscale-min-count'],
                   arg_group='Autoscale Configuration',
                   help='The minimal workernode count for Load-based atuoscale.')
        c.argument('autoscale_max_workernode_count', type=int,
                   options_list=['--autoscale-max-workernode-count', '--autoscale-max-count'],
                   arg_group='Autoscale Configuration',
                   help='The max workernode count for Load-based atuoscale.')
        c.argument('timezone', arg_group='Autoscale Configuration', validator=validate_timezone_name,
                   completer=get_generic_completion_list(AUTOSCALE_TIMEZONES),
                   help='The timezone for schedule autoscale type. Values from `az hdinsight autoscale list-timezones`')
        c.argument('days', nargs='+', arg_group='Autoscale Configuration',
                   arg_type=get_enum_type(week_days),
                   completer=get_generic_completion_list(week_days),
                   help='A space-delimited list of schedule day.')
        c.argument('time', arg_group='Autoscale Configuration', validator=validate_time,
                   help='The 24-hour time in the form of xx:xx in days.')
        c.argument('autoscale_workernode_count', type=int,
                   options_list=['--autoscale-workernode-count', '--autoscale-count'],
                   arg_group='Autoscale Configuration',
                   help='The scheduled workernode count.')

        # relay outbound and private link
        c.argument('resource_provider_connection', options_list=['--resource-provider-connection', '--rp-connection'],
                   arg_group='Resource provider connection',
                   arg_type=get_enum_type(ResourceProviderConnection), help='The resource provider connection type')
        c.argument('enable_private_link', arg_group='Private Link', arg_type=get_three_state_flag(),
                   help='Indicate whether enable the private link or not.')

        c.argument('private_link_configurations',
                   options_list=['--private-link-config', '--private-link-configurations'],
                   arg_group='Private Link', type=shell_safe_json_parse,
                   completer=FilesCompleter(),
                   help='The private link configurations when creating cluster. '
                        'Private Link Configurations may be supplied from a file using the `@{path}` syntax '
                        'or a JSON string. Please see https://github.com/Azure/azure-cli/blob/dev/src/azure-cli/azure'
                        '/cli/command_modules/hdinsight/tests/latest/privatelinkconfigurations.json')

        # compute isolation
        c.argument('enable_compute_isolation', options_list=['--enable-compute-isolation', '--compute-isolation'],
                   arg_group="Compute Isolation", arg_type=get_three_state_flag(),
                   help='Indicate whether enable compute isolation or not.')
        c.argument('host_sku', arg_group='Compute Isolation', help="The dedicated host sku of compute isolation.")

        # availability zones
        c.argument('zones', nargs='+', arg_group='Availability Zone',
                   help="A space-delimited list of availability zones where cluster will be created.")

        # resize
        with self.argument_context('hdinsight resize') as c:
            c.argument('target_instance_count', options_list=['--workernode-count', '-c'],
                       help='The target worker node instance count for the operation.', required=True)

        # application
        with self.argument_context('hdinsight application') as c:
            c.argument('cluster_name', options_list=['--cluster-name'],
                       completer=get_resource_name_completion_list('Microsoft.HDInsight/clusters'),
                       help='The name of the cluster.')
            c.argument('application_name', arg_type=name_type,
                       help='The constant value for the application name.')
            c.argument('application_type', options_list=['--type', '-t'],
                       arg_type=get_enum_type(['CustomApplication', 'RServer']),
                       help='The application type.')
            c.argument('marketplace_identifier', options_list=['--marketplace-id'],
                       help='The marketplace identifier.')
            c.argument('https_endpoint_access_mode', arg_group='HTTPS Endpoint',
                       options_list=['--access-mode'],
                       help='The access mode for the application.')
            c.argument('https_endpoint_destination_port', arg_group='HTTPS Endpoint',
                       options_list=['--destination-port'],
                       help='The destination port to connect to.')
            c.argument('sub_domain_suffix', arg_group='HTTPS Endpoint', help='The subdomain suffix of the application.')
            c.argument('disable_gateway_auth', arg_group='HTTPS Endpoint', arg_type=get_three_state_flag(),
                       help='Indicates whether to disable gateway authentication. '
                            'Default is to enable gateway authentication. Default: false. ')
            c.argument('tags', tags_type)
            c.argument('ssh_password', options_list=['--ssh-password', '-P'], arg_group='SSH',
                       help='SSH password for the cluster nodes.')

        # script action
        with self.argument_context('hdinsight script-action') as c:
            c.argument('cluster_name', options_list=['--cluster-name'],
                       completer=get_resource_name_completion_list('Microsoft.HDInsight/clusters'),
                       help='The name of the cluster.')
            c.argument('roles', nargs='+', completer=get_generic_completion_list(known_role_types),
                       help='A space-delimited list of roles (nodes) where the script will be executed. '
                            'Valid roles are {}.'.format(', '.join(known_role_types)))
            c.argument('persist_on_success', help='If the scripts needs to be persisted.')
            c.argument('script_action_name', arg_type=name_type, arg_group=None,
                       help='The name of the script action.')
            c.argument('script_uri', arg_group=None, help='The URI to the script.')
            c.argument('script_parameters', arg_group=None, help='The parameters for the script.')
            c.argument('script_execution_id', options_list=['--execution-id'], arg_group=None,
                       help='The script execution id')

        with self.argument_context('hdinsight script-action delete') as c:
            c.argument('script_name', arg_type=name_type, arg_group=None, help='The name of the script.')

        # Monitoring
        with self.argument_context('hdinsight monitor') as c:
            c.argument('workspace', validator=validate_workspace,
                       completer=get_resource_name_completion_list_under_subscription(
                           'Microsoft.OperationalInsights/workspaces'),
                       help='The name, resource ID or workspace ID of Log Analytics workspace.')
            c.argument('primary_key', help='The certificate for the Log Analytics workspace. '
                                           'Required when workspace ID is provided.')
            c.ignore('workspace_type')

        # Azure Monitor
        with self.argument_context('hdinsight azure-monitor') as c:
            c.argument('workspace', validator=validate_workspace,
                       completer=get_resource_name_completion_list_under_subscription(
                           'Microsoft.OperationalInsights/workspaces'),
                       help='The name, resource ID or workspace ID of Log Analytics workspace.')
            c.argument('primary_key', help='The certificate for the Log Analytics workspace. '
                                           'Required when workspace ID is provided.')
            c.ignore('workspace_type')

        with self.argument_context('hdinsight host') as c:
            c.argument('cluster_name', options_list=['--cluster-name'],
                       completer=get_resource_name_completion_list('Microsoft.HDInsight/clusters'),
                       help='The name of the cluster.')
            c.argument('hosts', options_list=['--host-names'], nargs='+',
                       help='A space-delimited list of host names that need to be restarted.')

        # autoscale
        autoscale_commands = ['create', 'update', 'delete', 'show']
        for command in autoscale_commands:
            with self.argument_context('hdinsight autoscale ' + command) as c:
                c.argument('cluster_name', options_list=['--cluster-name'],
                           completer=get_resource_name_completion_list('Microsoft.HDInsight/clusters'),
                           help='The name of the cluster.')

        for command in ['create', 'update']:
            with self.argument_context('hdinsight autoscale ' + command) as c:
                c.argument('min_workernode_count', type=int, arg_group='Load-based Autoscale',
                           help='The minimal workernode count for Load-based atuoscale.')
                c.argument('max_workernode_count', type=int, arg_group='Load-based Autoscale',
                           help='The max workernode count for Load-based atuoscale.')
                c.argument('timezone', arg_group='Schedule-based Autoscale', validator=validate_timezone_name,
                           completer=get_generic_completion_list(AUTOSCALE_TIMEZONES),
                           help='The timezone for schedule autoscale type. '
                                'Values from `az hdinsight autoscale list-timezones`')

        with self.argument_context('hdinsight autoscale create') as c:
            c.argument('type', arg_type=get_enum_type(known_autoscale_types), help='The autoscale type.')
            c.argument('days', nargs='+', arg_group='Schedule-based Autoscale',
                       arg_type=get_enum_type(week_days),
                       completer=get_generic_completion_list(week_days),
                       help='A space-delimited list of schedule day.')
            c.argument('time', arg_group='Schedule-based Autoscale', validator=validate_time,
                       help='The 24-hour time in the form xx:xx in days.')
            c.argument('workernode_count', type=int, options_list=['--workernode-count'],
                       arg_group='Schedule-based Autoscale',
                       help='The schedule workernode count.')
            c.argument('yes', options_list=['--yes', '-y'], help='Do not prompt for confirmation.', action='store_true')

        # autoscale condition
        autoscale_condition_commands = ['create', 'update', 'delete', 'list']
        for command in autoscale_condition_commands:
            with self.argument_context('hdinsight autoscale condition ' + command) as c:
                c.argument('cluster_name', options_list=['--cluster-name'],
                           completer=get_resource_name_completion_list('Microsoft.HDInsight/clusters'),
                           help='The name of the cluster.')

        for command in ['create', 'update']:
            with self.argument_context('hdinsight autoscale condition ' + command) as c:
                c.argument('days', nargs='+', arg_group=None, arg_type=get_enum_type(week_days),
                           completer=get_generic_completion_list(week_days),
                           help='A space-delimited list of schedule day.')
                c.argument('time', arg_group=None, validator=validate_time,
                           help='The 24-hour time in the form xx:xx in days.')
                c.argument('workernode_count', type=int, options_list=['--workernode-count'], arg_group=None,
                           help='The schedule workernode count.')
        for command in ['create', 'update']:
            with self.argument_context('hdinsight autoscale condition ' + command) as c:
                c.argument('index', type=int, help='The schedule condition index which starts with 0.')

        with self.argument_context('hdinsight autoscale condition delete') as c:
            c.argument('index', nargs='+', type=int,
                       help='The Space-separated list of condition indices which starts with 0 to delete.')
