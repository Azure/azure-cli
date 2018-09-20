# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps

# pylint: disable=line-too-long

helps['hdinsight'] = """
    type: group
    short-summary: Manage HDInsight clusters.
"""

helps['hdinsight create'] = """
    type: command
    short-summary: Creates a new cluster.
    examples:
        - name: Create a cluster with an existing storage account.
          text: |-
              az hdinsight cluster create -n MyCluster -g MyResourceGroup \\
              -u admin -p <password> -U sshuser -P <password> \\
              --storage-account myStorageAccount.blob.core.windows.net \\
              --storage-account-key <key> --storage-default-container default
"""
