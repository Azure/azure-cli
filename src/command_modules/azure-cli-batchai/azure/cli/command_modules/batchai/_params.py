# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from enum import Enum

from azure.cli.command_modules.vm._actions import get_vm_sizes
from azure.cli.core.commands.parameters import (
    ignore_type, location_type, resource_group_name_type, enum_choice_list, get_one_of_subscription_locations)
from azure.cli.core.sdk.util import ParametersContext
from azure.mgmt.storage.models import SkuName


def get_vm_size_completion_list(prefix, action, parsed_args, **kwargs):  # pylint: disable=unused-argument
    try:
        location = parsed_args.location
    except AttributeError:
        location = get_one_of_subscription_locations()
    result = get_vm_sizes(location)
    return [r.name for r in result]


class SupportedImages(Enum):  # pylint: disable=too-few-public-methods
    ubuntu_tls = "UbuntuLTS"
    ubuntu_dsvm = "UbuntuDSVM"


with ParametersContext(command='batchai cluster create') as c:
    c.register_alias('resource_group', options_list=('--resource-group', '-g'), arg_type=resource_group_name_type)
    c.argument('location', options_list=('--location', '-l'), arg_type=location_type,
               help='Location. You can configure the default location using `az configure --defaults '
                    'location=<location>` or specify it in the cluster configuration file.')
    c.register_alias('cluster_name', options_list=('--name', '-n'), help='Name of the cluster.')
    c.argument('user_name', options_list=('--user-name', '-u'),
               help='Name of the admin user to be created on every compute node.', arg_group='Admin Account')
    c.argument('ssh_key', options_list=('--ssh-key', '-k'),
               help='SSH public key value or path.', arg_group='Admin Account')
    c.argument('password', options_list=('--password', '-p'),
               help='Password.', arg_group='Admin Account')
    c.argument('image', options_list=('--image', '-i'), arg_group='Nodes',
               help='Operation system.', **enum_choice_list(SupportedImages))
    c.argument('vm_size', options_list=('--vm-size', '-s'),
               help='VM size (e.g. Standard_NC6 for 1 GPU node)', completer=get_vm_size_completion_list,
               arg_group='Nodes')
    c.argument('min_nodes', options_list=('--min',),
               help='Min nodes count.', type=int, arg_group='Nodes')
    c.argument('max_nodes', options_list=('--max',),
               help='Max nodes count.', type=int, arg_group='Nodes')
    c.argument('nfs_name', options_list=('--nfs',),
               help='Name of a file server to mount. If you need to mount more than one file server, configure them in '
                    'a configuration file and use --config option.',
               arg_group='File Server Mount')
    c.argument('nfs_resource_group', options_list=('--nfs-resource-group',),
               help='Resource group in which file server is created. Can be omitted if the file server and the cluster '
                    'belong to the same resource group',
               arg_group='File Server Mount')
    c.argument('nfs_mount_path', options_list=('--nfs-mount-path',),
               help='Relative mount path for nfs. The nfs will be available at '
                    '$AZ_BATCHAI_MOUNT_ROOT/<relative_mount_path> folder.',
               arg_group='File Server Mount')
    c.argument('azure_file_share', options_list=('--afs-name',),
               help='Name of the azure file share to mount. Please provide AZURE_BATCHAI_STORAGE_ACCOUNT and '
                    'AZURE_BATCHAI_STORAGE_KEY environment variables or add batchai/storage_key and '
                    'batchai/storage_account values to az configuration file containing storage account name and key.',
               arg_group='Azure File Share Mount')
    c.argument('afs_mount_path', options_list=('--afs-mount-path',),
               help='Relative mount path for Azure File share. The file share will be available at '
                    '$AZ_BATCHAI_MOUNT_ROOT/<relative_mount_path> folder. If you need to mount more than one Azure '
                    'Storage container, configure them in a configuration file and use --config option.',
               arg_group='Azure File Share Mount')
    c.argument('container_name', options_list=('--container-name',),
               help='Name of Azure Storage container to mount. Please provide AZURE_BATCHAI_STORAGE_ACCOUNT and '
                    'AZURE_BATCHAI_STORAGE_KEY environment variables or add batchai/storage_key and '
                    'batchai/storage_account values to az configuration file containing storage account name and key. '
                    'If you need to mount more than one Azure Storage container, configure them in a configuration '
                    'file and use --config option.',
               arg_group='Azure Storage Container Mount')
    c.argument('container_mount_path', options_list=('--container-mount-path',),
               help='Relative mount path for Azure Storage container. The container will be available at '
                    '$AZ_BATCHAI_MOUNT_ROOT/<relative_mount_path> folder.',
               arg_group='Azure Storage Container Mount')
    c.argument('json_file', options_list=('--config', '-c'),
               help='A path to a json file containing cluster create parameters '
                    '(json representation of azure.mgmt.batchai.models.ClusterCreateParameters).',
               arg_group='Advanced')

with ParametersContext(command='batchai cluster resize') as c:
    c.register_alias('resource_group', options_list=('--resource-group', '-g'), arg_type=resource_group_name_type)
    c.register_alias('cluster_name', options_list=('--name', '-n'), help='Name of the cluster.')
    c.argument('target', options_list=('--target', '-t'), help='Target number of compute nodes.')

with ParametersContext(command='batchai cluster auto-scale') as c:
    c.register_alias('resource_group', options_list=('--resource-group', '-g'), arg_type=resource_group_name_type)
    c.register_alias('cluster_name', options_list=('--name', '-n'), help='Name of the cluster.')
    c.argument('min_nodes', options_list=('--min',), help='Minimum number of nodes.')
    c.argument('max_nodes', options_list=('--max',), help='Maximum number of nodes.')

with ParametersContext(command='batchai cluster delete') as c:
    c.register_alias('resource_group', options_list=('--resource-group', '-g'), arg_type=resource_group_name_type)
    c.register_alias('cluster_name', options_list=('--name', '-n'), help='Name of the cluster.')

with ParametersContext(command='batchai cluster show') as c:
    c.register_alias('resource_group', options_list=('--resource-group', '-g'), arg_type=resource_group_name_type)
    c.register_alias('cluster_name', options_list=('--name', '-n'), help='Name of the cluster.')

with ParametersContext(command='batchai cluster list') as c:
    c.argument('resource_group', options_list=('--resource-group', '-g'), arg_type=resource_group_name_type)
    # Not implemented yet
    c.register_alias('clusters_list_options', options_list=('--clusters-list-options',), arg_type=ignore_type)

with ParametersContext(command='batchai cluster list-nodes') as c:
    c.register_alias('resource_group', options_list=('--resource-group', '-g'), arg_type=resource_group_name_type)
    c.register_alias('cluster_name', options_list=('--name', '-n'), help='Name of the cluster.')

with ParametersContext(command='batchai job create') as c:
    c.register_alias('resource_group', options_list=('--resource-group', '-g'), arg_type=resource_group_name_type)
    c.argument('location', options_list=('--location', '-l'), arg_type=location_type,
               help='Location. You can configure the default location using `az configure --defaults '
                    'location=<location>` or specify it in the job configuration file.')
    c.register_alias('job_name', options_list=('--name', '-n'), help='Name of the job.')
    c.argument('json_file', options_list=('--config', '-c'),
               help='A path to a json file containing job create parameters '
                    '(json representation of azure.mgmt.batchai.models.JobCreateParameters).')
    c.argument('cluster_name', options_list=('--cluster-name',),
               help='If specified, the job will run on the given cluster instead of the '
                    'one configured in the json file.')
    c.argument('cluster_resource_group', options_list=('--cluster-resource-group',),
               help='Specifies a resource group for the cluster given with --cluster-name parameter. '
                    'If omitted, --resource-group value will be used.')

with ParametersContext(command='batchai job terminate') as c:
    c.register_alias('resource_group', options_list=('--resource-group', '-g'), arg_type=resource_group_name_type)
    c.register_alias('job_name', options_list=('--name', '-n'), help='Name of the job.')

with ParametersContext(command='batchai job delete') as c:
    c.register_alias('resource_group', options_list=('--resource-group', '-g'), arg_type=resource_group_name_type)
    c.register_alias('job_name', options_list=('--name', '-n'), help='Name of the job.')

with ParametersContext(command='batchai job show') as c:
    c.register_alias('resource_group', options_list=('--resource-group', '-g'), arg_type=resource_group_name_type)
    c.register_alias('job_name', options_list=('--name', '-n'), help='Name of the job.')

with ParametersContext(command='batchai job list') as c:
    c.argument('resource_group', options_list=('--resource-group', '-g'), arg_type=resource_group_name_type)
    # Not implemented yet
    c.register_alias('jobs_list_options', options_list=('--jobs-list-options',), arg_type=ignore_type)

with ParametersContext(command='batchai job list-nodes') as c:
    c.register_alias('resource_group', options_list=('--resource-group', '-g'), arg_type=resource_group_name_type)
    c.register_alias('job_name', options_list=('--name', '-n'), help='Name of the job.')

with ParametersContext(command='batchai job list-files') as c:
    c.register_alias('resource_group', options_list=('--resource-group', '-g'), arg_type=resource_group_name_type)
    c.register_alias('job_name', options_list=('--name', '-n'), help='Name of the job.')
    c.register_alias('directory', options_list=('--output-directory-id', '-d'),
                     help='The Id of the Job output directory (as specified by "id" element in outputDirectories '
                          'collection in job create parameters). Use "stdouterr" to access job stdout and stderr '
                          'files.')

with ParametersContext(command='batchai job stream-file') as c:
    c.register_alias('resource_group', options_list=('--resource-group', '-g'), arg_type=resource_group_name_type)
    c.register_alias('job_name', options_list=('--job-name', '-j'), help='Name of the job.')
    c.register_alias('directory', options_list=('--output-directory-id', '-d'),
                     help='The Id of the Job output directory (as specified by "id" element in outputDirectories '
                          'collection in job create parameters). Use "stdouterr" to access job stdout and stderr '
                          'files.')
    c.argument('file_name', options_list=('--name', '-n'), help='The name of the file to stream.')

with ParametersContext(command='batchai file-server create') as c:
    c.register_alias('resource_group', options_list=('--resource-group', '-g'), arg_type=resource_group_name_type)
    c.argument('location', options_list=('--location', '-l'), arg_type=location_type,
               help='Location. You can configure the default location using `az configure --defaults '
                    'location=<location>` or specify it in the file server configuration file.')
    c.register_alias('file_server_name', options_list=('--name', '-n'), help='Name of the file server.')
    c.argument('vm_size', help='VM size.', completer=get_vm_size_completion_list)
    c.argument('disk_count', help='Number of disks.', type=int, arg_group='Storage')
    c.argument('disk_size', help='Disk size in Gb.', type=int, arg_group='Storage')
    c.argument('storage_sku', help='The sku of storage account to persist VM.',
               arg_group='Storage', **enum_choice_list(SkuName))
    c.argument('user_name', options_list=('--admin-user-name', '-u'),
               help='Name of the admin user to be created on every compute node.', arg_group='Admin Account')
    c.argument('ssh_key', options_list=('--ssh-key', '-k'),
               help='SSH public key value or path.', arg_group='Admin Account')
    c.argument('password', options_list=('--password', '-p'), help='Password.', arg_group='Admin Account')
    c.argument('json_file', options_list=('--config', '-c'),
               help='A path to a json file containing file server create parameters (json representation of '
                    'azure.mgmt.batchai.models.FileServerCreateParameters). Note, parameters given via command line '
                    'will overwrite parameters specified in the configuration file.', arg_group='Advanced')

with ParametersContext(command='batchai file-server show') as c:
    c.register_alias('resource_group', options_list=('--resource-group', '-g'), arg_type=resource_group_name_type)
    c.register_alias('file_server_name', options_list=('--name', '-n'), help='Name of the file server.')

with ParametersContext(command='batchai file-server delete') as c:
    c.register_alias('resource_group', options_list=('--resource-group', '-g'), arg_type=resource_group_name_type)
    c.register_alias('file_server_name', options_list=('--name', '-n'), help='Name of the file server.')

with ParametersContext(command='batchai file-server list') as c:
    c.argument('resource_group', options_list=('--resource-group', '-g'), arg_type=resource_group_name_type)
    # Not implemented yet
    c.register_alias('file_servers_list_options', options_list=('--file-servers-list-options',), arg_type=ignore_type)
