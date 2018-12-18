# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from knack.help_files import helps


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
              az hdinsight create -n MyCluster -g MyResourceGroup \\
              -p <HTTP password> \\
              --storage-account MyStorageAccount.blob.core.windows.net \\
              --storage-account-key <key>
"""

helps['hdinsight list'] = """
    type: command
    short-summary: List clusters in the resource group or subscription.
"""

helps['hdinsight wait'] = """
    type: command
    short-summary: Place the CLI in a waiting state until an operation is complete.
"""
