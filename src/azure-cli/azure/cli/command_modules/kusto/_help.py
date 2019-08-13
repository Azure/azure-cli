# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps

# pylint: disable=line-too-long

helps['kusto'] = """
    type: group
    short-summary: Manage Azure Kusto resources
"""

# Kusto cluster
helps['kusto cluster'] = """
    type: group
    short-summary: Manage Azure Kusto clusters.
"""

helps['kusto cluster create'] = """
    type: command
    short-summary: Create a Kusto cluster.
    examples:
       - name: Create a Kusto Cluster.
         text: |-
           az kusto cluster create -l "Central US" -n myclustername -g myrgname --sku D13_v2 --capacity 10
"""

helps['kusto cluster start'] = """
    type: command
    short-summary: Start a Kusto cluster.
    long-summary: When the cluster is restarted, it takes about ten minutes for it to become available (like when it was originally provisioned). It takes additional time for data to load into the hot cache.
"""

helps['kusto cluster stop'] = """
    type: command
    short-summary: Stop a Kusto cluster.
    long-summary: When the cluster is stopped, data is not available for queries, and you can't ingest new data. Start cluster to enable queries
"""

helps['kusto cluster update'] = """
    type: command
    short-summary: Update a Kusto cluster.
    examples:
       - name: update a Kusto Cluster.
         text: |-
           az kusto cluster update -n myclustername -g myrgname --sku D14_v2 --capacity 4
"""

helps['kusto cluster show'] = """
    type: command
    short-summary: Get a Kusto cluster.
"""

helps['kusto cluster list'] = """
    type: command
    short-summary: List a Kusto cluster.
"""

helps['kusto cluster delete'] = """
    type: command
    short-summary: Delete a Kusto cluster.
"""

helps['kusto cluster wait'] = """
    type: command
    short-summary: Wait for a managed Kusto cluster to reach a desired state.
    long-summary: If an operation on a cluster was interrupted or was started with `--no-wait`, use this command to
                  wait for it to complete.
"""


# Kusto database
helps['kusto database'] = """
    type: group
    short-summary: Manage Azure Kusto databases.
"""

helps['kusto database create'] = """
    type: command
    short-summary: Create a Kusto database.
    examples:
       - name: create a Kusto Database.
         text: |-
           az kusto database create --cluster-name myclustername -g myrgname -n mydbname  --soft-delete-period P365D --hot-cache-period P31D
"""


helps['kusto database update'] = """
    type: command
    short-summary: Update a Kusto database.
    examples:
      - name: create a Kusto Database.
        text: |-
          az kusto database update --cluster-name myclustername -g myrgname -n mydbname  --soft-delete-period P365D --hot-cache-period P30D
"""

helps['kusto database delete'] = """
    type: command
    short-summary: Delete a Kusto database.
"""

helps['kusto database list'] = """
    type: command
    short-summary: List a Kusto database.
"""

helps['kusto database show'] = """
    type: command
    short-summary: Get a Kusto database.
"""

helps['kusto database wait'] = """
    type: command
    short-summary: Wait for a managed Kusto database to reach a desired state.
    long-summary: If an operation on a database was interrupted or was started with `--no-wait`, use this command to
                  wait for it to complete.
"""
