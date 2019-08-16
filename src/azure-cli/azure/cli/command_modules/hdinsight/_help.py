# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps  # pylint: disable=unused-import
# pylint: disable=line-too-long, too-many-lines

helps['hdinsight'] = """
type: group
short-summary: Manage HDInsight resources.
"""

helps['hdinsight application'] = """
type: group
short-summary: Manage HDInsight applications.
"""

helps['hdinsight application wait'] = """
type: command
short-summary: Place the CLI in a waiting state until an operation is complete.
"""

helps['hdinsight list'] = """
type: command
short-summary: List HDInsight clusters in a resource group or subscription.
"""

helps['hdinsight monitor'] = """
type: group
short-summary: Manage Azure Monitor logs integration on an HDInsight cluster.
"""

helps['hdinsight monitor disable'] = """
type: command
short-summary: Disable the Azure Monitor logs integration on an HDInsight cluster.
"""

helps['hdinsight monitor enable'] = """
type: command
short-summary: Enable the Azure Monitor logs integration on an HDInsight cluster.
"""

helps['hdinsight monitor show'] = """
type: command
short-summary: Get the status of Azure Monitor logs integration on an HDInsight cluster.
"""

helps['hdinsight rotate-disk-encryption-key'] = """
type: command
short-summary: Rotate the disk encryption key of the specified HDInsight cluster.
"""

helps['hdinsight script-action'] = """
type: group
short-summary: Manage HDInsight script actions.
"""

helps['hdinsight script-action execute'] = """
type: command
short-summary: Execute script actions on the specified HDInsight cluster.
examples:
  - name: Execute a script action and persist on success.
    text: |-
        az hdinsight script-action execute -g MyResourceGroup -n MyScriptActionName \\
        --cluster-name MyCluster \\
        --script-uri https://hdiconfigactions.blob.core.windows.net/linuxgiraphconfigactionv01/giraph-installer-v01.sh \\
        --roles headnode workernode \\
        --persist-on-success
"""

helps['hdinsight wait'] = """
type: command
short-summary: Place the CLI in a waiting state until an operation is complete.
"""
