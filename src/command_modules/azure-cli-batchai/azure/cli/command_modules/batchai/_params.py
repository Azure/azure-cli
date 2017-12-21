# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from enum import Enum

from azure.cli.command_modules.vm._actions import get_vm_sizes
from azure.cli.core.commands.parameters import (
    get_enum_type, get_one_of_subscription_locations, resource_group_name_type)
from azure.cli.core.decorators import Completer
from azure.mgmt.storage.models import SkuName


@Completer
def get_vm_size_completion_list(cmd, prefix, namespace, **kwargs):  # pylint: disable=unused-argument
    try:
        location = namespace.location
    except AttributeError:
        location = get_one_of_subscription_locations(cmd.cli_ctx)
    result = get_vm_sizes(cmd.cli_ctx, location)
    return [r.name for r in result]


class SupportedImages(Enum):  # pylint: disable=too-few-public-methods
    ubuntu_tls = "UbuntuLTS"
    ubuntu_dsvm = "UbuntuDSVM"


# pylint: disable=line-too-long, too-many-statements
def load_arguments(self, _):

    with self.argument_context('batchai') as c:
        c.argument('resource_group', resource_group_name_type)

    with self.argument_context('batchai cluster') as c:
        c.argument('cluster_name', options_list=['--name', '-n'], help='Name of the cluster.')

    with self.argument_context('batchai cluster create') as c:
        c.argument('json_file', options_list=['--config', '-c'], help='A path to a json file containing cluster create parameters (json representation of azure.mgmt.batchai.models.ClusterCreateParameters).', arg_group='Advanced')

    with self.argument_context('batchai cluster create', arg_group='Admin Account') as c:
        c.argument('user_name', options_list=['--user-name', '-u'], help='Name of the admin user to be created on every compute node.')
        c.argument('ssh_key', options_list=['--ssh-key', '-k'], help='SSH public key value or path.')
        c.argument('password', options_list=['--password', '-p'], help='Password.')

    with self.argument_context('batchai cluster create', arg_group='Nodes') as c:
        c.argument('image', arg_type=get_enum_type(SupportedImages), options_list=['--image', '-i'], help='Operation system.')
        c.argument('vm_size', options_list=['--vm-size', '-s'], help='VM size (e.g. Standard_NC6 for 1 GPU node)', completer=get_vm_size_completion_list)
        c.argument('min_nodes', options_list=['--min'], help='Min nodes count.', type=int)
        c.argument('max_nodes', options_list=['--max'], help='Max nodes count.', type=int)

    with self.argument_context('batchai cluster create', arg_group='File Server Mount') as c:
        c.argument('nfs_name', options_list=['--nfs'], help='Name of a file server to mount. If you need to mount more than one file server, configure them in a configuration file and use --config option.')
        c.argument('nfs_resource_group', options_list=['--nfs-resource-group'], help='Resource group in which file server is created. Can be omitted if the file server and the cluster belong to the same resource group')
        c.argument('nfs_mount_path', options_list=['--nfs-mount-path'], help='Relative mount path for nfs. The nfs will be available at $AZ_BATCHAI_MOUNT_ROOT/<relative_mount_path> folder.')

    with self.argument_context('batchai cluster create', arg_group='Storage Account') as c:
        c.argument('account_name', options_list=['--storage-account-name'], help='Storage account name for Azure File Shares and/or Azure Storage Containers mounting. Related environment variable: AZURE_BATCHAI_STORAGE_ACCOUNT. Must be used in conjunction with --storage-account-key. If the key is not provided, the command will try to query the storage account key using the authenticated Azure account.')
        c.argument('account_key', options_list=['--storage-account-key'], help='Storage account key. Must be used in conjunction with --storage-account-name. Environment variable: AZURE_BATCHAI_STORAGE_KEY.')

    with self.argument_context('batchai cluster create', arg_group='Azure File Share Mount') as c:
        c.argument('azure_file_share', options_list=['--afs-name'], help='Name of the azure file share to mount. Must be used in conjunction with --storage-account-name and --storage-account-key arguments or AZURE_BATCHAI_STORAGE_ACCOUNT and AZURE_BATCHAI_STORAGE_KEY environment variables.  If you need to mount more than one Azure File share, configure them in a configuration file and use --config option.')
        c.argument('afs_mount_path', options_list=['--afs-mount-path'], help='Relative mount path for Azure File share. The file share will be available at $AZ_BATCHAI_MOUNT_ROOT/<relative_mount_path> folder.')

    with self.argument_context('batchai cluster create', arg_group='Azure Storage Container Mount') as c:
        c.argument('container_name', options_list=['--container-name'], help='Name of Azure Storage container to mount. Must be used in conjunction with --storage-account-name and --storage-account-key arguments or AZURE_BATCHAI_STORAGE_ACCOUNT and AZURE_BATCHAI_STORAGE_KEY environment variables. If you need to mount more than one Azure Storage container, configure them in a configuration file and use --config option.')
        c.argument('container_mount_path', options_list=['--container-mount-path'], help='Relative mount path for Azure Storage container. The container will be available at $AZ_BATCHAI_MOUNT_ROOT/<relative_mount_path> folder.')

    with self.argument_context('batchai cluster resize') as c:
        c.argument('target', options_list=['--target', '-t'], help='Target number of compute nodes.')

    with self.argument_context('batchai cluster auto-scale') as c:
        c.argument('min_nodes', options_list=['--min'], help='Minimum number of nodes.')
        c.argument('max_nodes', options_list=['--max'], help='Maximum number of nodes.')

    with self.argument_context('batchai cluster list') as c:
        # Not implemented yet
        c.ignore('clusters_list_options')

    with self.argument_context('batchai job') as c:
        c.argument('job_name', options_list=['--name', '-n'], help='Name of the job.')
        c.argument('cluster_name', options_list=['--cluster-name', '-r'], help='Name of the cluster.')
        c.argument('directory', options_list=['--output-directory-id', '-d'], help='The Id of the Job output directory (as specified by "id" element in outputDirectories collection in job create parameters). Use "stdouterr" to access job stdout and stderr files.')

    with self.argument_context('batchai job create') as c:
        c.argument('json_file', options_list=['--config', '-c'], help='A path to a json file containing job create parameters (json representation of azure.mgmt.batchai.models.JobCreateParameters).')
        c.argument('cluster_name', options_list=['--cluster-name', '-r'], help='If specified, the job will run on the given cluster instead of the one configured in the json file.')
        c.argument('cluster_resource_group', options_list=['--cluster-resource-group'], help='Specifies a resource group for the cluster given with --cluster-name parameter. If omitted, --resource-group value will be used.')

    with self.argument_context('batchai job list') as c:
        # Not implemented yet
        c.ignore('jobs_list_options')

    with self.argument_context('batchai job stream-file') as c:
        c.argument('job_name', options_list=['--job-name', '-j'], help='Name of the job.')
        c.argument('file_name', options_list=['--name', '-n'], help='The name of the file to stream.')

    with self.argument_context('batchai file-server') as c:
        c.argument('file_server_name', options_list=['--name', '-n'], help='Name of the file server.')

    with self.argument_context('batchai file-server create') as c:
        c.argument('vm_size', options_list=['--vm-size', '-s'], help='VM size.', completer=get_vm_size_completion_list)
        c.argument('json_file', options_list=['--config', '-c'], help='A path to a json file containing file server create parameters (json representation of azure.mgmt.batchai.models.FileServerCreateParameters). Note, parameters given via command line will overwrite parameters specified in the configuration file.', arg_group='Advanced')

    with self.argument_context('batchai file-server create', arg_group='Storage') as c:
        c.argument('disk_count', help='Number of disks.', type=int)
        c.argument('disk_size', help='Disk size in Gb.', type=int)
        c.argument('storage_sku', arg_type=get_enum_type(SkuName), help='The sku of storage account to persist VM.')

    with self.argument_context('batchai file-server create', arg_group='Admin Account') as c:
        c.argument('user_name', options_list=['--admin-user-name', '-u'], help='Name of the admin user to be created on every compute node.')
        c.argument('ssh_key', options_list=['--ssh-key', '-k'], help='SSH public key value or path.')
        c.argument('password', options_list=['--password', '-p'], help='Password.')

    with self.argument_context('batchai file-server list') as c:
        # Not implemented yet
        c.ignore('file_servers_list_options')
