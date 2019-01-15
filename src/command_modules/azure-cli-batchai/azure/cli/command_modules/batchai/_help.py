# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps

helps["batchai job file"] = """
"type": |-
    group
"short-summary": |-
    Commands to list and stream files in job's output directories.
"""

helps["batchai job list"] = """
"type": |-
    command
"short-summary": |-
    List jobs.
"examples":
-   "name": |-
        List jobs.
    "text": |-
        az batchai job list --resource-group MyResourceGroup --output json --experiment MyExperiment --workspace MyWorkspace
"""

helps["batchai cluster delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a cluster.
"""

helps["batchai workspace show"] = """
"type": |-
    command
"short-summary": |-
    Show information about a workspace.
"""

helps["batchai job node exec"] = """
"type": |-
    command
"short-summary": |-
    Executes a command line on a cluster's node used to execute the job with optional ports forwarding.
"""

helps["batchai job file stream"] = """
"type": |-
    command
"short-summary": |-
    Stream the content of a file (similar to 'tail -f').
"long-summary": |-
    Waits for the job to create the given file and starts streaming it similar to 'tail -f' command. The command completes when the job finished execution.
"examples":
-   "name": |-
        Stream the content of a file (similar to 'tail -f').
    "text": |-
        az batchai job file stream --file-name MyFile --job <job> --workspace <workspace> --experiment <experiment> --resource-group MyResourceGroup
"""

helps["batchai cluster node"] = """
"type": |-
    group
"short-summary": |-
    Commands to work with cluster nodes.
"""

helps["batchai job terminate"] = """
"type": |-
    command
"short-summary": |-
    Terminate a job.
"""

helps["batchai cluster node list"] = """
"type": |-
    command
"short-summary": |-
    List remote login information for cluster's nodes.
"long-summary": |-
    List remote login information for cluster nodes. You can ssh to a particular node using the provided public IP address and the port number.
    E.g. ssh <admin user name>@<public ip> -p <node's SSH port number>
"""

helps["batchai workspace create"] = """
"type": |-
    command
"short-summary": |-
    Create a workspace.
"""

helps["batchai file-server create"] = """
"type": |-
    command
"short-summary": |-
    Create a file server.
"""

helps["batchai workspace delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a workspace.
"""

helps["batchai cluster list"] = """
"type": |-
    command
"short-summary": |-
    List clusters.
"""

helps["batchai file-server list"] = """
"type": |-
    command
"short-summary": |-
    List file servers.
"""

helps["batchai job node list"] = """
"type": |-
    command
"short-summary": |-
    List remote login information for nodes which executed the job.
"long-summary": |-
    List remote login information for currently existing (not deallocated) nodes on which the job was executed. You can ssh to a particular node using the provided public IP address and the port number.
    E.g. ssh <admin user name>@<public ip> -p <node's SSH port number>
"""

helps["batchai job create"] = """
"type": |-
    command
"short-summary": |-
    Create a job.
"examples":
-   "name": |-
        Create a job.
    "text": |-
        az batchai job create --config-file <config-file> --cluster <cluster> --storage-account-name MyStorageAccount --name MyJob --resource-group MyResourceGroup --workspace <workspace> --experiment <experiment>
"""

helps["batchai"] = """
"type": |-
    group
"short-summary": |-
    Manage Batch AI resources.
"""

helps["batchai cluster auto-scale"] = """
"type": |-
    command
"short-summary": |-
    Set auto-scale parameters for a cluster.
"""

helps["batchai experiment show"] = """
"type": |-
    command
"short-summary": |-
    Show information about an experiment.
"""

helps["batchai cluster create"] = """
"type": |-
    command
"short-summary": |-
    Create a cluster.
"""

helps["batchai list-usages"] = """
"type": |-
    command
"short-summary": |-
    Gets the current usage information as well as limits for Batch AI resources for given location.
"""

helps["batchai experiment"] = """
"type": |-
    group
"short-summary": |-
    Commands to manage experiments.
"""

helps["batchai cluster node exec"] = """
"type": |-
    command
"short-summary": |-
    Executes a command line on a cluster's node with optional ports forwarding.
"""

helps["batchai cluster resize"] = """
"type": |-
    command
"short-summary": |-
    Resize a cluster.
"""

helps["batchai file-server delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a file server.
"""

helps["batchai workspace list"] = """
"type": |-
    command
"short-summary": |-
    List workspaces.
"""

helps["batchai file-server show"] = """
"type": |-
    command
"short-summary": |-
    Show information about a file server.
"""

helps["batchai job file list"] = """
"type": |-
    command
"short-summary": |-
    List job's output files in a directory with given id.
"long-summary": |-
    List job's output files in a directory with given id if the output directory is located on mounted Azure File Share or Blob Container.
"""

helps["batchai job delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a job.
"examples":
-   "name": |-
        Delete a job.
    "text": "az batchai job delete --workspace MyWorkspace --name MyJob --resource-group\
        \ MyResourceGroup --no-wait  --experiment MyExperiment --yes "
"""

helps["batchai job"] = """
"type": |-
    group
"short-summary": |-
    Commands to manage jobs.
"""

helps["batchai cluster"] = """
"type": |-
    group
"short-summary": |-
    Commands to manage clusters.
"""

helps["batchai job wait"] = """
"type": |-
    command
"short-summary": |-
    Waits for specified job completion and setups the exit code to the job's exit code.
"examples":
-   "name": |-
        Waits for specified job completion and setups the exit code to the job's exit code.
    "text": |-
        az batchai job wait --resource-group MyResourceGroup --workspace MyWorkspace --experiment <experiment> --name MyJob
"""

helps["batchai experiment delete"] = """
"type": |-
    command
"short-summary": |-
    Delete an experiment.
"""

helps["batchai cluster file list"] = """
"type": |-
    command
"short-summary": |-
    List files generated by the cluster's node setup task.
"long-summary": |-
    List files generated by the cluster's node setup task under $AZ_BATCHAI_STDOUTERR_DIR path. This functionality is available only if the node setup task output directory is located on mounted Azure File Share or Azure Blob Container.
"""

helps["batchai experiment create"] = """
"type": |-
    command
"short-summary": |-
    Create an experiment.
"examples":
-   "name": |-
        Create an experiment.
    "text": |-
        az batchai experiment create --workspace MyWorkspace --name MyExperiment --resource-group MyResourceGroup
"""

helps["batchai cluster show"] = """
"type": |-
    command
"short-summary": |-
    Show information about a cluster.
"examples":
-   "name": |-
        Show information about a cluster.
    "text": |-
        az batchai cluster show --output json --workspace MyWorkspace --name MyCluster --resource-group MyResourceGroup
"""

helps["batchai job show"] = """
"type": |-
    command
"short-summary": |-
    Show information about a job.
"""

helps["batchai cluster file"] = """
"type": |-
    group
"short-summary": |-
    Commands to work with files generated by node setup task.
"""

helps["batchai experiment list"] = """
"type": |-
    command
"short-summary": |-
    List experiments.
"""

helps["batchai workspace"] = """
"type": |-
    group
"short-summary": |-
    Commands to manage workspaces.
"""

helps["batchai job node"] = """
"type": |-
    group
"short-summary": |-
    Commands to work with nodes which executed a job.
"""

helps["batchai file-server"] = """
"type": |-
    group
"short-summary": |-
    Commands to manage file servers.
"""

