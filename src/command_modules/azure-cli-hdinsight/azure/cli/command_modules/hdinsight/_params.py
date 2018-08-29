# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from azure.cli.core.commands.parameters import get_enum_type, name_type


def load_arguments(self, _):
    from knack.arguments import CLIArgumentType
    node_size_type = CLIArgumentType(help='The size of the node. See also: https://docs.microsoft.com/en-us/azure/hdinsight/hdinsight-hadoop-provision-linux-clusters#configure-cluster-size')

    with self.argument_context('hdinsight cluster') as c:
        c.argument('cluster_name', arg_type=name_type,
                   help='The name of the cluster.')
        c.argument('cluster_version', options_list=['--version', '-v'],
                   help='The HDInsight cluster version. See also: https://docs.microsoft.com/en-us/azure/hdinsight/hdinsight-component-versioning#supported-hdinsight-versions')
        c.argument('cluster_type', options_list=['--type', '-t'],
                   help='Type of HDInsight cluster, e.g. Hadoop, InteractiveHive, MLServices, etc. See also: https://docs.microsoft.com/en-us/azure/hdinsight/hdinsight-hadoop-provision-linux-clusters#cluster-types')
        c.argument('cluster_tier', arg_type=get_enum_type(['standard', 'premium']),
                   help='The tier of the cluster, e.g. standard or premium.')
        c.argument('cluster_size', options_list=['--size', '-s'],
                   help='The number of worker nodes in the cluster.')
        c.argument('http_username', options_list=['--http-user', '-u'], arg_group='HTTP',
                   help='HTTP username for the cluster.')
        c.argument('http_password', options_list=['--http-password', '-p'], arg_group='HTTP',
                   help='HTTP password for the cluster.')
        c.argument('ssh_username', options_list=['--ssh-user', '-U'], arg_group='SSH',
                   help='SSH username for the cluster nodes.')
        c.argument('ssh_password', options_list=['--ssh-password', '-P'], arg_group='SSH',
                   help='SSH password for the cluster nodes.')
        c.argument('ssh_public_key', options_list=['--ssh-public-key', '-K'], arg_group='SSH',
                   help='SSH public key for the cluster nodes.')
        c.argument('headnode_size', arg_type=node_size_type)
        c.argument('workernode_size', arg_type=node_size_type)
        c.argument('zookeepernode_size', arg_type=node_size_type)
        c.argument('edgenode_size', arg_type=node_size_type)
        c.argument('storage_account', arg_group='Storage',
                   help='The storage account, e.g. <name>.blob.core.windows.net.')
        c.argument('storage_account_key', arg_group='Storage',
                   help='The storage account key.')
        c.argument('storage_default_container', arg_group='Storage',
                   help='The storage container the cluster will use.')
        c.argument('virtual_network', arg_group='Network',
                   help='The virtual network resource ID.')
        c.argument('subnet_name', arg_group='Network',
                   help='The name of the subnet in the specified virtual network.')
