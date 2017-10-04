# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.help_files import helps

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
"""

helps['batchai cluster resize'] = """
    type: command
    short-summary: Resize a cluster.
"""

helps['batchai cluster set-auto-scale-parameters'] = """
    type: command
    short-summary: Set auto-scale parameters for a cluster.
"""

helps['batchai cluster delete'] = """
    type: command
    short-summary: Delete a cluster.
"""

helps['batchai cluster list'] = """
    type: command
    short-summary: List clusters.
"""

helps['batchai cluster show'] = """
    type: command
    short-summary: Show information about a cluster.
"""

helps['batchai cluster list-nodes'] = """
    type: command
    short-summary: List remote login information for cluster's nodes.
"""

helps['batchai job'] = """
    type: group
    short-summary: Commands to manage jobs.
"""

helps['batchai job create'] = """
    type: command
    short-summary: Create a job.
"""

helps['batchai job terminate'] = """
    type: command
    short-summary: Terminate a job.
"""

helps['batchai job delete'] = """
    type: command
    short-summary: Delete a job.
"""

helps['batchai job list'] = """
    type: command
    short-summary: List jobs.
"""

helps['batchai job show'] = """
    type: command
    short-summary: Show information about a job.
"""

helps['batchai job list-nodes'] = """
    type: command
    short-summary: List remote login information for nodes on which the job was run.
"""

helps['batchai file list-files'] = """
    type: command
    short-summary: List job's output files in a directory with given id.
"""

helps['batchai stream-file'] = """
    type: command
    short-summary: Output the current content of the file and outputs appended data as the file grows
                   (similar to 'tail -f').
"""

helps['batchai file-server'] = """
    type: group
    short-summary: Commands to manage file servers.
"""

helps['batchai file-server create'] = """
    type: command
    short-summary: Create a file server.
"""

helps['batchai file-server delete'] = """
    type: command
    short-summary: Delete a file server.
"""

helps['batchai file-server list'] = """
    type: command
    short-summary: List file servers.
"""

helps['batchai file-server show'] = """
    type: command
    short-summary: Show information about a file server.
"""
