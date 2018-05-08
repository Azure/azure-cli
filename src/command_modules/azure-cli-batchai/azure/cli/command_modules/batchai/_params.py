# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from argcomplete import FilesCompleter
from azure.cli.command_modules.batchai import custom
from azure.cli.command_modules.vm._actions import get_vm_sizes
from azure.cli.core.commands.parameters import (
    get_enum_type, get_one_of_subscription_locations, resource_group_name_type, get_location_type)
from azure.cli.core.decorators import Completer


@Completer
def get_vm_size_completion_list(cmd, prefix, namespace, **kwargs):  # pylint: disable=unused-argument
    try:
        location = namespace.location
    except AttributeError:
        location = get_one_of_subscription_locations(cmd.cli_ctx)
    result = get_vm_sizes(cmd.cli_ctx, location)
    return [r.name for r in result]


# pylint: disable=line-too-long, too-many-statements
def load_arguments(self, _):

    with self.argument_context('batchai') as c:
        c.argument('resource_group', resource_group_name_type)

    with self.argument_context('batchai cluster') as c:
        c.argument('location', get_location_type(self.cli_ctx), help='Location in which to create the cluster. If the location is not specified and default location is not configured, will default to the resource group\'s location')
        c.argument('cluster_name', options_list=['--name', '-n'], help='Name of the cluster.')

    with self.argument_context('batchai cluster create') as c:
        c.argument('json_file', options_list=['--config', '-c'], help='A path to a json file containing cluster create parameters (json representation of azure.mgmt.batchai.models.ClusterCreateParameters).', arg_group='Advanced')

    with self.argument_context('batchai cluster create') as c:
        c.argument('setup_task', help='A command line which should be executed on each compute node when it\'s got allocated or rebooted. The task is executed under a user account added into sudoers list (so, it can use sudo). Note, if this parameter is specified, it will overwrite setup task given in the configuration file.', arg_group='Setup Task')
        c.argument('setup_task_output', help='Location of the folder where setup-task\'s logs will be stored. Required if setup-task argument is provided. Note, Batch AI will create create several helper folders under this location. The created folders are reported as stdOutErrPathSuffix by get cluster command.', arg_group='Setup Task')

    with self.argument_context('batchai cluster create', arg_group='Virtual Network') as c:
        c.argument('subnet', options_list=['--subnet'], help='Resource id of a virtual network subnet to put the cluster in.')

    with self.argument_context('batchai cluster create', arg_group='Admin Account') as c:
        c.argument('user_name', options_list=['--user-name', '-u'], help='Name of the admin user account to be created on each compute node. If the value is not provided and no user configuration is provided in the config file, current user\'s name will be used.')
        c.argument('ssh_key', options_list=['--ssh-key', '-k'], help='SSH public key value or path. If the value is not provided and no ssh public key or password is configured in the config file the default public ssh key (~/.ssh/id_rsa.pub) of the current user will be used (if available).', completer=FilesCompleter())
        c.argument('generate_ssh_keys', action='store_true', help='Generate SSH public and private key files if missing. The keys will be stored in the ~/.ssh directory.')
        c.argument('password', options_list=['--password', '-p'], help='Password.')

    with self.argument_context('batchai cluster create', arg_group='Auto Storage') as c:
        c.argument('use_auto_storage', action='store_true', help='If provided, the command will create a storage account in a new or existing resource group named "batchaiautostorage". It will also create Azure File Share with name "batchaishare", Azure Blob Container with name "batchaicontainer". The File Share and Blob Container will be mounted on each cluster node at $AZ_BATCHAI_MOUNT_ROOT/autoafs and $AZ_BATCHAI_MOUNT_ROOT/autobfs. If the resource group already exists and contains an approapriate storage account belonging to the same region as cluster, this command will reuse existing storage account.')

    with self.argument_context('batchai cluster create', arg_group='Nodes') as c:
        c.argument('image', options_list=['--image', '-i'], help='Operation system image for cluster nodes. The value may contain an alias ({0}) or specify image details in the form "publisher:offer:sku:version". If image configuration is not provided via command line or configuration file, Batch AI will choose default OS image'.format(', '.join(custom.SUPPORTED_IMAGE_ALIASES.keys())))
        c.argument('custom_image', help='Resource id of a virtual machine image to be used for nodes creation. Note, you need to provide --image with which this image was created.')
        c.argument('vm_size', options_list=['--vm-size', '-s'], help='VM size for cluster nodes (e.g. Standard_NC6 for 1 GPU node)', completer=get_vm_size_completion_list)
        c.argument('target', options_list=['--target', '-t'], help='Number of nodes which should be allocated immediately after cluster creation. If the cluster is in auto-scale mode, BatchAI can change the number of nodes later based on number of running and queued jobs.')
        c.argument('min_nodes', options_list=['--min'], help='Min nodes count for the auto-scale cluster.', type=int)
        c.argument('max_nodes', options_list=['--max'], help='Max nodes count for the auto-scale cluster.', type=int)
        c.argument('vm_priority', arg_type=get_enum_type(['dedicated', 'lowpriority']), options_list=['--vm-priority'], help="VM priority. If lowpriority selected the node can get preempted while the job is running.")

    with self.argument_context('batchai cluster create', arg_group='File Server Mount') as c:
        c.argument('nfs_name', options_list=['--nfs-name', '--nfs'], help='Name of a file server to mount on each cluster node. If you need to mount more than one file server, configure them in a configuration file and use --config option.')
        c.argument('nfs_resource_group', options_list=['--nfs-resource-group'], help='Resource group in which file server is created. Can be omitted if the file server and the cluster belong to the same resource group')
        c.argument('nfs_mount_path', options_list=['--nfs-mount-path'], help='Relative mount path for NFS. The NFS will be available at $AZ_BATCHAI_MOUNT_ROOT/<relative_mount_path> folder.')

    with self.argument_context('batchai cluster create', arg_group='Storage Account') as c:
        c.argument('account_name', options_list=['--storage-account-name'], help='Storage account name for Azure File Shares and/or Azure Storage Containers to be mounted on each cluster node. Related environment variable: AZURE_BATCHAI_STORAGE_ACCOUNT. Must be used in conjunction with --storage-account-key. If the key is not provided, the command will try to query the storage account key using the authenticated Azure account.')
        c.argument('account_key', options_list=['--storage-account-key'], help='Storage account key. Must be used in conjunction with --storage-account-name. Environment variable: AZURE_BATCHAI_STORAGE_KEY. Optional if the storage account belongs to the current subscription.')

    with self.argument_context('batchai cluster create', arg_group='Azure File Share Mount') as c:
        c.argument('azure_file_share', options_list=['--afs-name'], help='Name of the Azure File Share to be mounted on each cluster node. Must be used in conjunction with --storage-account-name and --storage-account-key arguments or AZURE_BATCHAI_STORAGE_ACCOUNT and AZURE_BATCHAI_STORAGE_KEY environment variables. If you need to mount more than one Azure File Share, configure them in a configuration file and use --config option.')
        c.argument('afs_mount_path', options_list=['--afs-mount-path'], help='Relative mount path for Azure File share. The file share will be available at $AZ_BATCHAI_MOUNT_ROOT/<relative_mount_path> folder.')

    with self.argument_context('batchai cluster create', arg_group='Azure Storage Container Mount') as c:
        c.argument('container_name', options_list=['--bfs-name', '--container-name'], help='Name of Azure Storage container to be mounted on each cluster node. Must be used in conjunction with --storage-account-name and --storage-account-key arguments or AZURE_BATCHAI_STORAGE_ACCOUNT and AZURE_BATCHAI_STORAGE_KEY environment variables. If you need to mount more than one Azure Storage Blob Container, configure them in a configuration file and use --config option.')
        c.argument('container_mount_path', options_list=['--bfs-mount-path', '--container-mount-path'], help='Relative mount path for Azure Storage container. The container will be available at $AZ_BATCHAI_MOUNT_ROOT/<relative_mount_path> folder.')

    with self.argument_context('batchai cluster resize') as c:
        c.argument('target', options_list=['--target', '-t'], help='Target number of compute nodes.')

    with self.argument_context('batchai cluster auto-scale') as c:
        c.argument('min_nodes', options_list=['--min'], help='Minimum number of nodes.')
        c.argument('max_nodes', options_list=['--max'], help='Maximum number of nodes.')

    with self.argument_context('batchai cluster list-files') as c:
        c.argument('path', options_list=['--path', '-p'], help='Relative path of a subfolder inside of node setup task output directory.')
        c.argument('expiry', options_list=['--expiry', '-e'], help='Time in minutes for how long generated download URLs should remain valid.')

    with self.argument_context('batchai cluster list') as c:
        # Not implemented yet
        c.ignore('clusters_list_options')

    with self.argument_context('batchai job') as c:
        c.argument('location', get_location_type(self.cli_ctx), help='Location in which to create the job. If default location is not configured, will default to the resource group\'s location')
        c.argument('job_name', options_list=['--name', '-n'], help='Name of the job.')
        c.argument('cluster_name', options_list=['--cluster-name', '-r'], help='Name of the cluster.')

    with self.argument_context('batchai job create') as c:
        c.argument('json_file', options_list=['--config', '-c'], help='A path to a json file containing job create parameters (json representation of azure.mgmt.batchai.models.JobCreateParameters).')
        c.argument('cluster_name', options_list=['--cluster-name', '-r'], help='If specified, the job will run on the given cluster instead of the one configured in the json file.')
        c.argument('cluster_resource_group', options_list=['--cluster-resource-group'], help='Specifies a resource group for the cluster given with --cluster-name parameter. If omitted, --resource-group value will be used.')

    with self.argument_context('batchai job create', arg_group='Azure File Share Mount') as c:
        c.argument('azure_file_share', options_list=['--afs-name'], help='Name of the Azure File Share to mount during the job execution. The File Share will be mounted only on the nodes which are executing the job. Must be used in conjunction with --storage-account-name and --storage-account-key arguments or AZURE_BATCHAI_STORAGE_ACCOUNT and AZURE_BATCHAI_STORAGE_KEY environment variables. If you need to mount more than one Azure File share, configure them in a configuration file and use --config option.')
        c.argument('afs_mount_path', options_list=['--afs-mount-path'], help='Relative mount path for Azure File Share. The File Share will be available at $AZ_BATCHAI_JOB_MOUNT_ROOT/<relative_mount_path> folder.')

    with self.argument_context('batchai job create', arg_group='Azure Storage Container Mount') as c:
        c.argument('container_name', options_list=['--bfs-name'], help='Name of Azure Storage Blob Container to mount during the job execution. The container will be mounted only on the nodes which are executing the job. Must be used in conjunction with --storage-account-name and --storage-account-key arguments or AZURE_BATCHAI_STORAGE_ACCOUNT and AZURE_BATCHAI_STORAGE_KEY environment variables. If you need to mount more than one Azure Storage container, configure them in a configuration file and use --config option.')
        c.argument('container_mount_path', options_list=['--bfs-mount-path'], help='Relative mount path for Azure Storage Blob Container. The container will be available at $AZ_BATCHAI_JOB_MOUNT_ROOT/<relative_mount_path> folder.')

    with self.argument_context('batchai job create', arg_group='Storage Account') as c:
        c.argument('account_name', options_list=['--storage-account-name'], help='Storage account name for Azure File Shares and/or Azure Storage Containers to be mounted. Related environment variable: AZURE_BATCHAI_STORAGE_ACCOUNT. Must be used in conjunction with --storage-account-key. If the key is not provided, the command will try to query the storage account key using the authenticated Azure account.')
        c.argument('account_key', options_list=['--storage-account-key'], help='Storage account key. Must be used in conjunction with --storage-account-name. Environment variable: AZURE_BATCHAI_STORAGE_KEY.')

    with self.argument_context('batchai job create', arg_group='File Server Mount') as c:
        c.argument('nfs_name', options_list=['--nfs-name'], help='Name of a file server to mount during the job execution. The NFS will be mounted only on the nodes which are executing the job. If you need to mount more than one file server, configure them in a configuration file and use --config option.')
        c.argument('nfs_resource_group', options_list=['--nfs-resource-group'], help='Resource group in which file server is created. Can be omitted if the file server and the job belong to the same resource group.')
        c.argument('nfs_mount_path', options_list=['--nfs-mount-path'], help='Relative mount path for NFS. The NFS will be available at $AZ_BATCHAI_JOB_MOUNT_ROOT/<relative_mount_path> folder.')

    with self.argument_context('batchai job list') as c:
        # Not implemented yet
        c.ignore('jobs_list_options')

    with self.argument_context('batchai job file stream') as c:
        c.argument('output_directory_id', options_list=['--output-directory-id', '-d'], help='The Id of the job\'s output directory (as specified by "id" element in outputDirectories collection in the job create parameters).')
        c.argument('file_name', options_list=['--file-name', '-f'], help='The name of the file to stream.')
        c.argument('path', options_list=['--path', '-p'], help='Relative path in the given output directory.')

    with self.argument_context('batchai job file list') as c:
        c.argument('output_directory_id', options_list=['--output-directory-id', '-d'], help='The Id of the job\'s output directory (as specified by "id" element in outputDirectories collection in the job create parameters).')
        c.argument('path', options_list=['--path', '-p'], help='Relative path in the given output directory.')
        c.argument('expiry', options_list=['--expiry', '-e'], type=int, help='Time in minutes for how long generated download URL should remain valid.')

    with self.argument_context('batchai job wait') as c:
        c.argument('check_interval_sec', options_list=['--interval'], help="Polling interval in sec.")

    with self.argument_context('batchai file-server') as c:
        c.argument('location', get_location_type(self.cli_ctx), help='Location in which to create the file server. If default location is not configured, will default to the resource group\'s location')
        c.argument('file_server_name', options_list=['--name', '-n'], help='Name of the file server.')

    with self.argument_context('batchai file-server create') as c:
        c.argument('vm_size', options_list=['--vm-size', '-s'], help='VM size.', completer=get_vm_size_completion_list)
        c.argument('json_file', options_list=['--config', '-c'], help='A path to a json file containing file server create parameters (json representation of azure.mgmt.batchai.models.FileServerCreateParameters). Note, parameters given via command line will overwrite parameters specified in the configuration file.', arg_group='Advanced')

    with self.argument_context('batchai file-server create', arg_group='Storage Disks') as c:
        c.argument('disk_count', help='Number of disks.', type=int)
        c.argument('disk_size', help='Disk size in Gb.', type=int)
        c.argument('caching_type', arg_type=get_enum_type(['none', 'readonly', 'readwrite']), help='Caching type for premium disks. If not provided via command line or in configuration file, no caching will be used.')
        c.argument('storage_sku', arg_type=get_enum_type(['Premium_LRS', 'Standard_LRS']), help='The sku of storage account to persist VM.')

    with self.argument_context('batchai file-server create', arg_group='Admin Account') as c:
        c.argument('user_name', options_list=['--user-name', '-u'], help='Name of the admin user account to be created on NFS node. If the value is not provided and no user configuration is provided in the config file, current user\'s name will be used.')
        c.argument('ssh_key', options_list=['--ssh-key', '-k'], help='SSH public key value or path. If the value is not provided and no ssh public key or password is configured in the config file the default public ssh key (~/.ssh/id_rsa.pub) of the current user will be used (if available).', completer=FilesCompleter())
        c.argument('generate_ssh_keys', action='store_true', help='Generate SSH public and private key files if missing. The keys will be stored in the ~/.ssh directory.')
        c.argument('password', options_list=['--password', '-p'], help='Password.')

    with self.argument_context('batchai file-server create', arg_group='Virtual Network') as c:
        c.argument('subnet', options_list=['--subnet'], help='Resource id of a virtual network subnet to put the file server in. If not provided via command line or in configuration file, Batch AI will create a new virtual network and subnet under your subscription.')

    with self.argument_context('batchai file-server list') as c:
        # Not implemented yet
        c.ignore('file_servers_list_options')
