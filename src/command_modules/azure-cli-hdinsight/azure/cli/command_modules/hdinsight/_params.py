# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands.parameters import get_enum_type, name_type, tags_type, get_resource_name_completion_list, \
    get_generic_completion_list
from ._validators import validate_component_version

# Cluster types may be added in the future. Therefore, this list can be used for completion, but not input validation.
known_cluster_types = ["hadoop", "interactivehive", "hbase", "kafka", "storm", "spark", "rserver", "mlservices"]
known_role_types = ["headnode", "workernode", "zookeepernode", "edgenode"]


# pylint: disable=too-many-statements
def load_arguments(self, _):
    from ._completers import storage_account_completion_list, storage_account_key_completion_list
    from knack.arguments import CLIArgumentType
    node_size_type = CLIArgumentType(arg_group='Node',
                                     help='The size of the node. See also: https://docs.microsoft.com/en-us/azure/'
                                          'hdinsight/hdinsight-hadoop-provision-linux-clusters#configure-cluster-size')

    # cluster
    with self.argument_context('hdinsight') as c:
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
        c.argument('cluster_tier', arg_type=get_enum_type(['standard', 'premium']), arg_group='Cluster',
                   help='The tier of the cluster: standard or premium.')
        c.argument('http_username', options_list=['--http-user', '-u'], arg_group='HTTP',
                   help='HTTP username for the cluster.  Default: admin.')
        c.argument('http_password', options_list=['--http-password', '-p'], arg_group='HTTP',
                   help='HTTP password for the cluster.')
        c.argument('ssh_username', options_list=['--ssh-user', '-U'], arg_group='SSH',
                   help='SSH username for the cluster nodes.')
        c.argument('ssh_password', options_list=['--ssh-password', '-P'], arg_group='SSH',
                   help='SSH password for the cluster nodes. If none specified, uses the HTTP password.')
        c.argument('ssh_public_key', options_list=['--ssh-public-key', '-K'], arg_group='SSH',
                   help='SSH public key for the cluster nodes.')
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
        c.argument('workernode_count', options_list=['--size', '-s'], arg_group='Cluster',
                   help='The number of worker nodes in the cluster.')
        c.argument('storage_account', arg_group='Storage', completer=storage_account_completion_list,
                   help='The storage account, e.g. "<name>.blob.core.windows.net".')
        c.argument('storage_account_key', arg_group='Storage', completer=storage_account_key_completion_list,
                   help='The storage account key. A key can be retrieved automatically '
                        'if the user has access to the storage account.')
        c.argument('storage_default_container', arg_group='Storage',
                   help='The storage container the cluster will use. '
                        'Uses the cluster name if none was specified. (WASB only)')
        c.argument('storage_default_filesystem', arg_group='Storage',
                   help='The storage filesystem the cluster will use. (DFS only)')
        c.argument('virtual_network', arg_group='Network',
                   help='The virtual network resource ID of an existing virtual network.')
        c.argument('subnet_name', arg_group='Network',
                   help='The name of the subnet in the specified virtual network.')
        c.argument('script_action_name', arg_group='Script Action', help='The name of the script action.')
        c.argument('script_uri', arg_group='Script Action', help='The URI to the script.')
        c.argument('script_parameters', arg_group='Script Action', help='The parameters for the script.')

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
