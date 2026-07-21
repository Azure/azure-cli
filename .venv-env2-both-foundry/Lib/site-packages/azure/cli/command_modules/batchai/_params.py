# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from argcomplete import FilesCompleter
from azure.cli.command_modules.batchai import custom
from azure.cli.core.commands.parameters import (
    get_enum_type, get_one_of_subscription_locations, resource_group_name_type, get_location_type)
from azure.cli.core.decorators import Completer


def get_vm_sizes(cli_ctx, location):
    from azure.cli.core.profiles import ResourceType
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    client_factory = get_mgmt_service_client(cli_ctx, ResourceType.MGMT_COMPUTE)
    return list(client_factory.virtual_machine_sizes.list(location))


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
        c.argument('workspace_name', id_part='name', options_list=['--workspace', '-w'], help='Name of workspace.')

    with self.argument_context('batchai workspace') as c:
        c.argument('location', get_location_type(self.cli_ctx), help='Location of the workspace. If omitted, the location of the resource group will be used.')
        c.argument('workspace_name', options_list=['--workspace', '-n'], id_part='name', help='Name of workspace.')

    with self.argument_context('batchai cluster') as c:
        c.argument('cluster_name', options_list=['--name', '-n'], id_part='child_name_1', help='Name of cluster.')

    with self.argument_context('batchai cluster create') as c:
        c.argument('json_file', options_list=['--config-file', '-f'], help='A path to a json file containing cluster create parameters (json representation of azure.mgmt.batchai.models.ClusterCreateParameters).', arg_group='Advanced')

    with self.argument_context('batchai cluster create') as c:
        c.argument('setup_task', help='A command line which should be executed on each compute node when it\'s got allocated or rebooted. The task is executed in a bash subshell under root account.', arg_group='Setup Task')
        c.argument('setup_task_output', help='Directory path to store where setup-task\'s logs. Note, Batch AI will create several helper directories under this path. The created directories are reported as stdOutErrPathSuffix by \'az cluster show\' command.', arg_group='Setup Task')

    with self.argument_context('batchai cluster create', arg_group='Virtual Network') as c:
        c.argument('subnet', options_list=['--subnet'], help='ARM ID of a virtual network subnet to put the cluster in.')

    with self.argument_context('batchai cluster create', arg_group='Admin Account') as c:
        c.argument('user_name', options_list=['--user-name', '-u'], help='Name of admin user account to be created on each compute node. If the value is not provided and no user configuration is provided in the config file, current user\'s name will be used.')
        c.argument('ssh_key', options_list=['--ssh-key', '-k'], help='Optional SSH public key value or path. If ommited and no password specified, default SSH key (~/.ssh/id_rsa.pub) will be used.', completer=FilesCompleter())
        c.argument('generate_ssh_keys', action='store_true', help='Generate SSH public and private key files in ~/.ssh directory (if missing).')
        c.argument('password', options_list=['--password', '-p'], help='Optional password for the admin user account to be created on each compute node.')

    with self.argument_context('batchai cluster create', arg_group='Auto Storage') as c:
        c.argument('use_auto_storage', action='store_true', help='If provided, the command will create a storage account in a new or existing resource group named "batchaiautostorage". It will also create Azure File Share with name "batchaishare", Azure Blob Container with name "batchaicontainer". The File Share and Blob Container will be mounted on each cluster node at $AZ_BATCHAI_MOUNT_ROOT/autoafs and $AZ_BATCHAI_MOUNT_ROOT/autobfs. If the resource group already exists and contains an approapriate storage account belonging to the same region as cluster, this command will reuse existing storage account.')

    with self.argument_context('batchai cluster create', arg_group='Nodes') as c:
        c.argument('image', options_list=['--image', '-i'], help='Operation system image for cluster nodes. The value may contain an alias ({0}) or specify image details in the form "publisher:offer:sku:version". If image configuration is not provided via command line or configuration file, Batch AI will choose default OS image'.format(', '.join(custom.SUPPORTED_IMAGE_ALIASES.keys())))
        c.argument('custom_image', help='ARM ID of a virtual machine image to be used for nodes creation. Note, you need to provide --image containing information about the base image used for this image creation.')
        c.argument('vm_size', options_list=['--vm-size', '-s'], help='VM size for cluster nodes (e.g. Standard_NC6 for 1 GPU node)', completer=get_vm_size_completion_list)
        c.argument('target', options_list=['--target', '-t'], help='Number of nodes which should be allocated immediately after cluster creation. If the cluster is in auto-scale mode, BatchAI can change the number of nodes later based on number of running and queued jobs.')
        c.argument('min_nodes', options_list=['--min'], help='Min nodes count for the auto-scale cluster.', type=int)
        c.argument('max_nodes', options_list=['--max'], help='Max nodes count for the auto-scale cluster.', type=int)
        c.argument('vm_priority', arg_type=get_enum_type(['dedicated', 'lowpriority']), options_list=['--vm-priority'], help="VM priority.")

    with self.argument_context('batchai cluster create', arg_group='File Server Mount') as c:
        c.argument('nfs', options_list=['--nfs'], help='Name or ARM ID of a file server to be mounted on each cluster node. You need to provide full ARM ID if the file server belongs to a different workspace. Multiple NFS can be mounted using configuration file (see --config-file option).')
        c.argument('nfs_mount_path', options_list=['--nfs-mount-path'], help='Relative mount path for NFS. The NFS will be available at `$AZ_BATCHAI_MOUNT_ROOT/<relative_mount_path>` folder.')

    with self.argument_context('batchai cluster create', arg_group='Azure Storage Mount') as c:
        c.argument('account_name', options_list=['--storage-account-name'], help='Storage account name for Azure File Shares and/or Azure Storage Containers to be mounted on each cluster node. Can be specified using AZURE_BATCHAI_STORAGE_ACCOUNT environment variable.')
        c.argument('account_key', options_list=['--storage-account-key'], help='Storage account key. Required if the storage account belongs to a different subscription. Can be specified using AZURE_BATCHAI_STORAGE_KEY environment variable.')
        c.argument('azure_file_share', options_list=['--afs-name'], help='Name of Azure File Share to be mounted on each cluster node. Must be used in conjunction with --storage-account-name. Multiple shares can be mounted using configuration file (see --config-file option).')
        c.argument('afs_mount_path', options_list=['--afs-mount-path'], help='Relative mount path for Azure File share. The file share will be available at `$AZ_BATCHAI_MOUNT_ROOT/<relative_mount_path>` folder.')
        c.argument('container_name', options_list=['--bfs-name'], help='Name of Azure Storage container to be mounted on each cluster node. Must be used in conjunction with --storage-account-name. Multiple containers can be mounted using configuration file (see --config-file option).')
        c.argument('container_mount_path', options_list=['--bfs-mount-path'], help='Relative mount path for Azure Storage container. The container will be available at `$AZ_BATCHAI_MOUNT_ROOT/<relative_mount_path>` folder.')

    with self.argument_context('batchai cluster resize') as c:
        c.argument('target', options_list=['--target', '-t'], help='Target number of compute nodes.')

    with self.argument_context('batchai cluster auto-scale') as c:
        c.argument('min_nodes', options_list=['--min'], help='Minimum number of nodes.')
        c.argument('max_nodes', options_list=['--max'], help='Maximum number of nodes.')

    for group in ['batchai cluster file', 'batchai cluster node']:
        with self.argument_context(group) as c:
            c.argument('cluster_name', options_list=['--cluster', '-c'], id_part=None, help='Name of cluster.')
            c.argument('workspace_name', id_part=None, options_list=['--workspace', '-w'], help='Name of workspace.')

    with self.argument_context('batchai cluster file list') as c:
        c.argument('path', options_list=['--path', '-p'], help='Relative path of a subfolder inside of the node setup task output directory.')
        c.argument('expiry', options_list=['--expiry'], help='Time in minutes for how long generated download URLs should remain valid.')

    with self.argument_context('batchai cluster list') as c:
        c.argument('workspace_name', options_list=['--workspace', '-w'], id_part=None, help='Name of workspace.')
        c.ignore('clusters_list_options')

    with self.argument_context('batchai experiment') as c:
        c.argument('experiment_name', options_list=['--name', '-n'], id_part='resource_name', help='Name of experiment.')
        c.argument('workspace_name', options_list=['--workspace', '-w'], id_part='name', help='Name of workspace.')

    with self.argument_context('batchai experiment list') as c:
        c.argument('workspace_name', id_part=None, options_list=['--workspace', '-w'], help='Name of workspace.')
        c.ignore('experiments_list_by_workspace_options')

    with self.argument_context('batchai job') as c:
        c.argument('job_name', options_list=['--name', '-n'], id_part='resource_name', help='Name of job.')
        c.argument('experiment_name', options_list=['--experiment', '-e'], id_part='child_name_1', help='Name of experiment.')

    with self.argument_context('batchai job create') as c:
        c.argument('json_file', options_list=['--config-file', '-f'], help='A path to a json file containing job create parameters (json representation of azure.mgmt.batchai.models.JobCreateParameters).')
        c.argument('cluster', options_list=['--cluster', '-c'], help='Name or ARM ID of the cluster to run the job. You need to provide ARM ID if the cluster belongs to a different workspace.')

    with self.argument_context('batchai job create', arg_group='Azure Storage Mount') as c:
        c.argument('account_name', options_list=['--storage-account-name'], help='Storage account name for Azure File Shares and/or Azure Storage Containers to be mounted on each cluster node. Can be specified using AZURE_BATCHAI_STORAGE_ACCOUNT environment variable.')
        c.argument('account_key', options_list=['--storage-account-key'], help='Storage account key. Required if the storage account belongs to a different subscription. Can be specified using AZURE_BATCHAI_STORAGE_KEY environment variable.')
        c.argument('azure_file_share', options_list=['--afs-name'], help='Name of Azure File Share to mount during the job execution. The File Share will be mounted only on the nodes which are executing the job. Must be used in conjunction with --storage-account-name.  Multiple shares can be mounted using configuration file (see --config-file option).')
        c.argument('afs_mount_path', options_list=['--afs-mount-path'], help='Relative mount path for Azure File Share. The File Share will be available at `$AZ_BATCHAI_JOB_MOUNT_ROOT/<relative_mount_path>` folder.')
        c.argument('container_name', options_list=['--bfs-name'], help='Name of Azure Storage Blob Container to mount during the job execution. The container will be mounted only on the nodes which are executing the job. Must be used in conjunction with --storage-account-name. Multiple containers can be mounted using configuration file (see --config-file option).')
        c.argument('container_mount_path', options_list=['--bfs-mount-path'], help='Relative mount path for Azure Storage Blob Container. The container will be available at `$AZ_BATCHAI_JOB_MOUNT_ROOT/<relative_mount_path>` folder.')

    with self.argument_context('batchai job create', arg_group='File Server Mount') as c:
        c.argument('nfs', options_list=['--nfs'], help='Name or ARM ID of the file server to be mounted during the job execution. You need to provide ARM ID if the file server belongs to a different workspace. You can configure multiple file servers using job\'s  configuration file.')
        c.argument('nfs_mount_path', options_list=['--nfs-mount-path'], help='Relative mount path for NFS. The NFS will be available at `$AZ_BATCHAI_JOB_MOUNT_ROOT/<relative_mount_path>` folder.')

    with self.argument_context('batchai job list') as c:
        c.argument('workspace_name', id_part=None, options_list=['--workspace', '-w'], help='Name of workspace.')
        c.argument('experiment_name', options_list=['--experiment', '-e'], id_part=None, help='Name of experiment.')
        c.ignore('jobs_list_by_experiment_options')

    for group in ['batchai job file', 'batchai job node']:
        with self.argument_context(group) as c:
            c.argument('job_name', options_list=['--job', '-j'], id_part=None, help='Name of job.')
            c.argument('workspace_name', id_part=None, options_list=['--workspace', '-w'], help='Name of workspace.')
            c.argument('experiment_name', options_list=['--experiment', '-e'], id_part=None, help='Name of experiment.')
            c.argument('output_directory_id', options_list=['--output-directory-id', '-d'], help='The Id of the job\'s output directory (as specified by "id" element in outputDirectories collection in the job create parameters).')
            c.argument('path', options_list=['--path', '-p'], help='Relative path in the given output directory.')

    with self.argument_context('batchai job file stream') as c:
        c.argument('file_name', options_list=['--file-name', '-f'], help='The name of the file to stream.')

    with self.argument_context('batchai job file list') as c:
        c.argument('expiry', options_list=['--expiry'], type=int, help='Time in minutes for how long generated download URL should remain valid.')

    with self.argument_context('batchai job wait') as c:
        c.argument('check_interval_sec', options_list=['--interval'], help="Polling interval in sec.")

    for group in ['batchai cluster node exec', 'batchai job node exec']:
        with self.argument_context(group) as c:
            c.argument('cmdline', options_list=['--exec'], help='Optional command line to be executed on the node. If not provided, the command will perform ports forwarding only.')
            c.argument('node_id', options_list=['--node-id', '-n'], help='ID of the node to forward the ports to. If not provided, the command will be executed on the first available node.')
            c.argument('ports', options_list=['--address', '-L'], action='append', help='Specifies that connections to the given TCP port or Unix socket on the local (client) host are to be forwarded to the given host and port, or Unix socket, on the remote side. e.g. -L 8080:localhost:8080')
            c.argument('password', options_list=['--password', '-p'], help='Optional password to establish SSH connection.')
            c.argument('ssh_private_key', options_list=['--ssh-private-key', '-k'], help='Optional SSH private key path to establish SSH connection. If omitted, the default SSH private key will be used.')

    with self.argument_context('batchai file-server') as c:
        c.argument('resource_group', options_list=['--resource-group', '-g'], configured_default='default_workspace_resource_group', id_part='resource_group', help='Name of resource group. You can configure a default value by setting up default workspace using `az batchai workspace set-default`.')
        c.argument('workspace', options_list=['--workspace', '-w'], configured_default='default_workspace_name', id_part='name', help='Name or ARM ID of the workspace. You can configure default workspace using `az batchai workspace set-default`')
        c.argument('file_server_name', options_list=['--name', '-n'], id_part='child_name_1', help='Name of file server.')

    with self.argument_context('batchai file-server create') as c:
        c.argument('vm_size', options_list=['--vm-size', '-s'], help='VM size.', completer=get_vm_size_completion_list)
        c.argument('json_file', options_list=['--config-file', '-f'], help='A path to a json file containing file server create parameters (json representation of azure.mgmt.batchai.models.FileServerCreateParameters). Note, parameters given via command line will overwrite parameters specified in the configuration file.', arg_group='Advanced')

    with self.argument_context('batchai file-server create', arg_group='Storage Disks') as c:
        c.argument('disk_count', help='Number of disks.', type=int)
        c.argument('disk_size', help='Disk size in Gb.', type=int)
        c.argument('caching_type', arg_type=get_enum_type(['none', 'readonly', 'readwrite']), help='Caching type for premium disks. If not provided via command line or in configuration file, no caching will be used.')
        c.argument('storage_sku', arg_type=get_enum_type(['Premium_LRS', 'Standard_LRS']), help='The sku of storage account to persist VM.')

    with self.argument_context('batchai file-server create', arg_group='Admin Account') as c:
        c.argument('user_name', options_list=['--user-name', '-u'], help='Name of admin user account to be created on NFS node. If the value is not provided and no user configuration is provided in the config file, current user\'s name will be used.')
        c.argument('ssh_key', options_list=['--ssh-key', '-k'], help='Optional SSH public key value or path. If ommited and no password specified, default SSH key (~/.ssh/id_rsa.pub) will be used.', completer=FilesCompleter())
        c.argument('generate_ssh_keys', action='store_true', help='Generate SSH public and private key files in ~/.ssh directory (if missing).')
        c.argument('password', options_list=['--password', '-p'], help='Optional password for the admin user created on the NFS node.')

    with self.argument_context('batchai file-server create', arg_group='Virtual Network') as c:
        c.argument('subnet', options_list=['--subnet'], help='ARM ID of a virtual network subnet to put the file server in. If not provided via command line or in the configuration file, Batch AI will create a new virtual network and subnet under your subscription.')

    with self.argument_context('batchai file-server list') as c:
        c.argument('workspace_name', options_list=['--workspace', '-w'], id_part=None, help='Name of workspace.')
        c.ignore('file_servers_list_by_workspace_options')
