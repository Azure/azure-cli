# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps

helps['batchai'] = """
    type: group
    short-summary: Batch AI.
"""

helps['batchai cluster'] = """
    type: group
    short-summary: Commands to manage clusters.
"""

helps['batchai cluster create'] = """
    type: command
    short-summary: Create a cluster.
    long-summary:
        Please refer to https://github.com/Azure/BatchAI/blob/master/documentation/using-azure-cli-20.md for
        the documentation.
    examples:
        - name: (Recommended approach) Create a cluster using a configuration file.
          text: >
            az batchai cluster create -n MyCluster -g MyResourceGroup -c cluster.json
        - name: Create a cluster using a configuration file and override admin user account settings.
          text: |
            az batchai cluster create -n MyCluster -g MyResourceGroup -c cluster.json \\
                -u $USER -k ~/.ssh/id_rsa.pub
        - name: Create a single node GPU cluster with default image, given ssh key and with auto-storage account.
          text: |
            az batchai cluster create -n MyCluster -g MyResourceGroup --use-auto-storage \\
                -s Standard_NC6 -t 1 -k id_rsa.pub
        - name:
            Create a cluster with a setup command which installs unzip on every node, the command output will be
            stored on auto storage account Azure File Share.
          text: |
            az batchai cluster create -n MyCluster -g MyResourceGroup --use-auto-storage \\
                -s Standard_NC6 -t 1 -k id_rsa.pub \\
                --setup-task 'sudo apt update; sudo apt install unzip' \\
                --setup-task-output '$AZ_BATCHAI_MOUNT_ROOT/autoafs'
        - name: Create a cluster providing all parameters manually.
          text: |
            az batchai cluster create -n MyCluster -g MyResourceGroup \\
                -i UbuntuDSVM -s Standard_NC6 --vm-priority lowpriority \\
                --min 0 --target 1 --max 10 \\
                --nfs-name MyNfsToMount --afs-name MyAzureFileShareToMount --bfs-name MyBlobContainerNameToMount \\
                -u $USER -k ~/.ssh/id_rsa.pub -p ImpossibleToGuessPassword

"""

helps['batchai cluster resize'] = """
    type: command
    short-summary: Resize a cluster.
    examples:
        - name: Resize a cluster to zero size to stop paying for it.
          text:
            az batchai cluster resize -n MyCluster -g MyResourceGroup -t 0
        - name: Resize a cluster to have 10 nodes.
          text:
            az batchai cluster resize -n MyCluster -g MyResourceGroup -t 10
"""

helps['batchai cluster auto-scale'] = """
    type: command
    short-summary: Set auto-scale parameters for a cluster.
    examples:
        - name: Make a cluster to auto scale between 0 and 10 nodes depending on number of queued and running jobs.
          text:
            az batchai auto-scale -n MyCluster -g MyResourceGroup --min 0 --max 10
"""

helps['batchai cluster delete'] = """
    type: command
    short-summary: Delete a cluster.
    examples:
        - name: Delete a cluster and wait for deletion to be completed.
          text:
            az batchai cluster delete -n MyCluster -g MyResourceGroup
        - name: Send a delete command for a cluster and do not wait for deletion to be completed.
          text:
            az batchai cluster delete -n MyCluster -g MyResourceGroup --no-wait
        - name: Delete cluster without asking for confirmation (for non-interactive scenarios).
          text:
            az batchai cluster delete -n MyCluster -g MyResourceGroup -y
"""

helps['batchai cluster list'] = """
    type: command
    short-summary: List clusters.
    examples:
        - name: List all clusters under the current subscription.
          text:
            az batchai cluster list -o table
        - name: List all clusters under the current subscription belonging to the given resource group.
          text:
            az batchai cluster list -g MyResourceGroup -o table
"""

helps['batchai cluster show'] = """
    type: command
    short-summary: Show information about a cluster.
    examples:
        - name: Show full information about a cluster.
          text:
            az batchai cluster show -n MyCluster -g MyResourceGroup
        - name: Show brief information about a cluster.
          text:
            az batchai cluster show -n MyCluster -g MyResourceGroup -o table
"""

helps['batchai cluster list-nodes'] = """
    type: command
    short-summary: List remote login information for cluster's nodes.
    long-summary:
        List remote login information for cluster nodes - node id, public ip and ssh port. All cluster nodes share
        the same public IP. You can ssh to a particular node using the provided public IP and the port number. \n
        E.g. ssh <admin user name>@<public ip> -p <node's port number>
    examples:
        - name: List remote login information for a cluster.
          text:
            az batchai cluster list-nodes -n MyCluster -g MyResourceGroup -o table
"""

helps['batchai cluster list-files'] = """
    type: command
    short-summary: List files generated by the cluster's node setup task.
    long-summary:
        List files generated by the cluster's node setup task under $AZ_BATCHAI_STDOUTERR_DIR path. This functionality is
        available only if the node setup task output directory is located on mounted Azure File Share or Azure Blob Container.
    examples:
        - name: List names and sizes of files and directories inside of $AZ_BATCHAI_STDOUTERR_DIR.
          text:
            az batchai cluster list-files -n MyCluster -g MyResourceGroup -o table
        - name: List names, sizes and download URLs for files and directories inside of $AZ_BATCHAI_STDOUTERR_DIR.
          text:
            az batchai cluster list-files -n MyCluster -g MyResourceGroup
        - name:
            List names, sizes and download URLs for files and directories inside of $AZ_BATCHAI_STDOUTERR_DIR/folder/subfolder.
          text:
            az batchai cluster list-files -n MyCluster -g MyResourceGroup -p folder/subfolder
        - name:
            List names, sizes and download URLs for files and directories inside of $AZ_BATCHAI_STDOUTERR_DIR making
            download URLs to remain valid for one hour.
          text:
            az batchai cluster list-files -n MyCluster -g MyResourceGroup -e 60
"""

helps['batchai job'] = """
    type: group
    short-summary: Commands to manage jobs.
"""

helps['batchai job create'] = """
    type: command
    short-summary: Create a job.
    long-summary:
        Please refer to https://github.com/Azure/BatchAI/blob/master/documentation/using-azure-cli-20.md for
        the documentation.
    examples:
        - name:
            Create a job using a configuration file and submit it for running on a cluster in the same resource
            group.
          text:
            az batchai job create -n MyJob -r MyCluster -g MyResourceGroup -c job.json
        - name:
            Create a job using a configuration file and submit it for running on a cluster in a different resource
            group.
          text: |
            az batchai job create -n MyJob -g MyJobResourceGroup -c job.json \\
                -r MyCluster --cluster-resource-group MyClusterResourceGroup
"""

helps['batchai job terminate'] = """
    type: command
    short-summary: Terminate a job.
    examples:
        - name: Terminate a job and wait for the job to be terminated.
          text:
            az batchai job terminate -n MyJob -g MyResourceGroup
        - name: Terminate a job without asking for confirmation (for non-interactive scenarios).
          text:
            az batchai job terminate -n MyJob -g MyResourceGroup -y
        - name: Request job termination without waiting for the job to be terminated.
          text:
            az batchai job terminate -n MyJob -g MyResourceGroup --no-wait
"""

helps['batchai job delete'] = """
    type: command
    short-summary: Delete a job.
    examples:
        - name: Delete a job. The job will be terminated if it's currently running.
          text:
            az batchai job delete -n MyJob -g MyResourceGroup
        - name: Delete a job without asking for confirmation (for non-interactive scenarios).
          text:
            az batchai job delete -n MyJob -g MyResourceGroup -y
        - name: Request job deletion without waiting for job to be deleted.
          text:
            az batchai job delete -n MyJob -g MyResourceGroup --no-wait
"""

helps['batchai job list'] = """
    type: command
    short-summary: List jobs.
    examples:
        - name: List all jobs under current subscription.
          text:
            az batchai job list -o table
        - name: List all jobs under current subscription in the given resource group.
          text:
            az batchai job list -g MyResourceGroup -o table
"""

helps['batchai job show'] = """
    type: command
    short-summary: Show information about a job.
    examples:
        - name: Show full information about a job.
          text:
            az batchai job show -n MyJob -g MyResourceGroup
        - name: Show brief information about a job.
          text:
            az batchai job show -n MyJob -g MyResourceGroup -o table
"""

helps['batchai job list-nodes'] = """
    type: command
    short-summary: List remote login information for nodes on which the job was run.
    long-summary:
        List remote login information about currently existing (not deallocated) nodes on which the job was executed.
        The information includes node id, public ip and ssh port number. All cluster nodes are sharing the same public
        IP. You can ssh to a particular node using the provided public IP and the port number.\n
        E.g. ssh <admin user name>@<public ip> -p <node's port number>

"""

helps['batchai job file'] = """
    type: group
    short-summary: Commands to list and stream files in jobs' output directories.
"""

helps['batchai job file list'] = """
    type: command
    short-summary: List job's output files in a directory with given id.
    long-summary:
         List job's output files in a directory with given id if the output directory is located on mounted Azure File
         Share or Blob Container.
    examples:
        - name:
            List files and directories with their parameters and download URLs in the root of the standard output
            directory of the job.
          text:
            az batchai job file list -n MyJob -g MyResourceGroup
        - name:
            List files and directories with their parameters and download URLs in a folder 'MyFolder/MySubfolder' of an
            output directory with id 'MODELS'.
          text:
            az batchai job file list -n MyJob -g MyResourceGroup -d MODELS -p MyFolder/MySubfolder
        - name:
            List name and sizes for files and directories in the root of the standard output directory of the job.
          text:
            az batchai job file list -n MyJob -g MyResourceGroup -o table
        - name:
            List files and directories with their parameters and download URLs in the root of the standard output
            directory of the job making download URLs to remain valid for one hour.
          text:
            az batchai job file list -n MyJob -g MyResourceGroup -e 60
"""

helps['batchai job file stream'] = """
    type: command
    short-summary: Output the current content of the file and outputs appended data as the file grows
                   (similar to 'tail -f').
    long-summary:
        Wait for the job to create the given file and starts streaming it similar to 'tail -f' command. The command
        completes when the job finished execution, being deleted or terminated.
    examples:
        - name: Stream standard output file of the job.
          text:
            az batchai job file stream -n MyJob -g MyResourceGroup -f stdout.txt
        - name: Stream a file 'log.txt' from a folder 'logs' of an output directory with id 'OUTPUTS'.
          text:
            az batchai job file stream -n MyJob -g MyResourceGroup -d OUTPUTS -p logs -f log.txt
"""

helps['batchai file-server'] = """
    type: group
    short-summary: Commands to manage file servers.
"""

helps['batchai file-server create'] = """
    type: command
    short-summary: Create a file server.
    long-summary:
        Please refer to https://github.com/Azure/BatchAI/blob/master/documentation/using-azure-cli-20.md for
        the documentation.
    examples:
        - name: Create a NFS file server using a configuration file.
          text:
            az batchai file-server create -n MyNFS -g MyResourceGroup -c nfs.json
        - name: Create a NFS manually providing parameters.
          text: |
            az file-server create -n MyNFS -g MyResourceGroup \\
                -s Standard_D14 --disk-count 4 --disk-size 512 \\
                --storage-sku Premium_LRS --caching-type readonly \\
                -u $USER -k ~/.ssh/id_rsa.pub
"""

helps['batchai file-server delete'] = """
    type: command
    short-summary: Delete a file server.
    examples:
        - name: Delete file server and wait for deletion to be completed.
          text:
            az batchai file-server delete -n MyNFS -g MyResourceGroup
        - name: Delete file server without asking for confirmation (for non-interactive scenarios).
          text:
            az batchai file-server delete -n MyNFS -g MyResourceGroup -y
        - name: Request file server deletion without waiting for deletion to be completed.
          text:
            az batchai file-server delete -n MyNFS -g MyResourceGroup --no-wait
"""

helps['batchai file-server list'] = """
    type: command
    short-summary: List file servers.
    examples:
        - name: List all file servers under the current subscription.
          text:
            az batchai file-server list -o table
        - name: List all file servers in the given resource group under the current subscription.
          text:
            az batchai file-server list -g MyResourceGroup -o table
"""

helps['batchai file-server show'] = """
    type: command
    short-summary: Show information about a file server.
    examples:
        - name: Show full information about a file server.
          text:
            az batchai file-server show -n MyNFS -g MyResourceGroup
        - name: Show brief information about a file server.
          text:
            az batchai file-server show -n MyNFS -g MyResourceGroup -o table

"""

helps['batchai list-usages'] = """
    type: command
    short-summary:
        Gets the current usage information as well as limits for Batch AI resources for given location.
    examples:
        - name: Get information for eastus location.
          text:
            az batchai list-usages -l eastus -o table
"""
