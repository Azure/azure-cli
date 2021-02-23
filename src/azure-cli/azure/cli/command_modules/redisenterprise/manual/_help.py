# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
# pylint: disable=too-many-lines

from knack.help_files import helps


helps['redisenterprise operation-status'] = """
    type: group
    short-summary: Manage Redis Enterprise operation status
"""

helps['redisenterprise operation-status show'] = """
    type: command
    short-summary: Get the status of an operation
    examples:
      - name: Get the status of an operation.
        text: |-
               az redisenterprise operation-status show --operation-id "testoperationid" --location "West US"
"""

helps['redisenterprise'] = """
    type: group
    short-summary: Manage dedicated Redis Enterprise caches for your Azure applications
"""

helps['redisenterprise list'] = """
    type: command
    short-summary: List Redis Enterprise caches
    long-summary: List details about all caches within current Subscription or provided Resource Group
    examples:
      - name: List all Redis Enterprise caches in a resource group.
        text: |-
               az redisenterprise list --resource-group "rg1"
      - name: List all Redis Enterprise caches within the current subscription.
        text: |-
               az redisenterprise list
"""

helps['redisenterprise show'] = """
    type: command
    short-summary: Get information about a Redis Enterprise cache
    examples:
      - name: Get information about a Redis Enterprise cache.
        text: |-
               az redisenterprise show --cluster-name "cache1" --resource-group "rg1"
"""

helps['redisenterprise create'] = """
    type: command
    short-summary: Create new Redis Enterprise cache instance
    long-summary: Create or update an existing (overwrite/recreate, with potential downtime) cache cluster \
with an associated database
    parameters:
      - name: --persistence
        short-summary: "Persistence settings"
        long-summary: |
            Usage: --persistence aof-enabled=XX aof-frequency=XX rdb-enabled=XX rdb-frequency=XX

            aof-enabled: Sets whether AOF is enabled.  Allowed values: true, false.
            aof-frequency: Sets the frequency at which data is written to disk.  Allowed values: 1s, always.
            rdb-enabled: Sets whether RDB is enabled.  Allowed values: true, false.
            rdb-frequency: Sets the frequency at which a snapshot of the database is created.  Allowed values: \
1h, 6h, 12h.

            After enabling persistence, you will be unable to disable it. Support for disabling persistence after \
enabling will be added at a later date.
      - name: --modules
        short-summary: "Optional set of redis modules to enable in this database - modules can only be added at \
creation time."
        long-summary: |
            Usage: --modules name=XX args=XX

            name: Required. The name of the module, e.g. 'RedisBloom', 'RediSearch', 'RedisTimeSeries'
            args: Configuration options for the module, e.g. 'ERROR_RATE 0.00 INITIAL_SIZE 400'.

            Multiple actions can be specified by using more than one --modules argument.
    examples:
      - name: Create new Redis Enterprise cache cluster with database.
        text: |-
               az redisenterprise create --cluster-name "cache1" --location "East US" --minimum-tls-version "1.2" \
--sku "Enterprise_E20" --capacity 4 --tags tag1="value1" --zones "1" "2" "3" --client-protocol "Encrypted" \
--clustering-policy "EnterpriseCluster" --eviction-policy "NoEviction" --modules name="RedisBloom" args="ERROR_RATE \
0.00 INITIAL_SIZE 400" --modules name="RedisTimeSeries" args="RETENTION_POLICY 20" --modules name="RediSearch" \
--persistence aof-enabled=true aof-frequency="1s" --port 10000 --resource-group "rg1"
      - name: Create new Redis Enterprise cache cluster without database (warning - the cache will not be usable \
until you create a database).
        text: |-
               az redisenterprise create --cluster-name "cache1" --location "West US" --minimum-tls-version "1.2" \
--sku "EnterpriseFlash_F300" --capacity 3 --tags tag1="value1" --zones "1" "2" "3" --resource-group "rg1" \
--no-database
"""

helps['redisenterprise update'] = """
    type: command
    short-summary: Update an existing Redis Enterprise cache cluster
    examples:
      - name: Update an existing Redis Enterprise cache cluster.
        text: |-
               az redisenterprise update --cluster-name "cache1" --minimum-tls-version "1.2" --sku \
"EnterpriseFlash_F300" --capacity 9 --tags tag1="value1" --resource-group "rg1"
"""

helps['redisenterprise delete'] = """
    type: command
    short-summary: Delete a Redis Enterprise cache
    examples:
      - name: Delete a Redis Enterprise cache.
        text: |-
               az redisenterprise delete --cluster-name "cache1" --resource-group "rg1"
"""

helps['redisenterprise wait'] = """
    type: command
    short-summary: Place the CLI in a waiting state until a condition of the Redis Enterprise cache cluster is met
    examples:
      - name: Pause executing next line of CLI script until the Redis Enterprise cache cluster is successfully created.
        text: |-
               az redisenterprise wait --cluster-name "cache1" --resource-group "rg1" --created
      - name: Pause executing next line of CLI script until the Redis Enterprise cache cluster is successfully updated.
        text: |-
               az redisenterprise wait --cluster-name "cache1" --resource-group "rg1" --updated
      - name: Pause executing next line of CLI script until the Redis Enterprise cache is successfully deleted.
        text: |-
               az redisenterprise wait --cluster-name "cache1" --resource-group "rg1" --deleted
"""

helps['redisenterprise database'] = """
    type: group
    short-summary: Manage Redis Enterprise databases
"""

helps['redisenterprise database list'] = """
    type: command
    short-summary: List all databases in a Redis Enterprise cache
    long-summary: List details about all databases in the specified Redis Enterprise cache
    examples:
      - name: List all databases in the specified Redis Enterprise cache.
        text: |-
               az redisenterprise database list --cluster-name "cache1" --resource-group "rg1"
"""

helps['redisenterprise database show'] = """
    type: command
    short-summary: Get information about a database in a Redis Enterprise cache
    examples:
      - name: Get information about a database in a Redis Enterprise cache.
        text: |-
               az redisenterprise database show --cluster-name "cache1" --resource-group "rg1"
"""

helps['redisenterprise database create'] = """
    type: command
    short-summary: Create new database for a Redis Enterprise cache
    parameters:
      - name: --persistence
        short-summary: "Persistence settings"
        long-summary: |
            Usage: --persistence aof-enabled=XX aof-frequency=XX rdb-enabled=XX rdb-frequency=XX

            aof-enabled: Sets whether AOF is enabled.  Allowed values: true, false.
            aof-frequency: Sets the frequency at which data is written to disk.  Allowed values: 1s, always.
            rdb-enabled: Sets whether RDB is enabled.  Allowed values: true, false.
            rdb-frequency: Sets the frequency at which a snapshot of the database is created.  Allowed values: \
1h, 6h, 12h.

            After enabling persistence, you will be unable to disable it. Support for disabling persistence after \
enabling will be added at a later date.
      - name: --modules
        short-summary: "Optional set of redis modules to enable in this database - modules can only be added at \
creation time."
        long-summary: |
            Usage: --modules name=XX args=XX

            name: Required. The name of the module, e.g. 'RedisBloom', 'RediSearch', 'RedisTimeSeries'
            args: Configuration options for the module, e.g. 'ERROR_RATE 0.00 INITIAL_SIZE 400'.

            Multiple actions can be specified by using more than one --modules argument.
    examples:
      - name: Create new database for a Redis Enterprise cache.
        text: |-
               az redisenterprise database create --cluster-name "cache1" --client-protocol "Encrypted" \
--clustering-policy "EnterpriseCluster" --eviction-policy "AllKeysLRU" --modules name="RedisBloom" args="ERROR_RATE \
0.00 INITIAL_SIZE 400" --modules name="RedisTimeSeries" args="RETENTION_POLICY 20" --modules name="RediSearch" \
--persistence aof-enabled=true aof-frequency="1s" --port 10000 --resource-group "rg1"
"""

helps['redisenterprise database update'] = """
    type: command
    short-summary: Update an existing Redis Enterprise database
    parameters:
      - name: --persistence
        short-summary: "Persistence settings"
        long-summary: |
            Usage: --persistence aof-enabled=XX aof-frequency=XX rdb-enabled=XX rdb-frequency=XX

            aof-enabled: Sets whether AOF is enabled.  Allowed values: true, false.
            aof-frequency: Sets the frequency at which data is written to disk.  Allowed values: 1s, always.
            rdb-enabled: Sets whether RDB is enabled.  Allowed values: true, false.
            rdb-frequency: Sets the frequency at which a snapshot of the database is created.  Allowed values: \
1h, 6h, 12h.

            After enabling persistence, you will be unable to disable it. Support for disabling persistence after \
enabling will be added at a later date.
    examples:
      - name: Update an existing Redis Enterprise database.
        text: |-
               az redisenterprise database update --cluster-name "cache1" --client-protocol "Encrypted" \
--eviction-policy "AllKeysLRU" --persistence rdb-enabled=true rdb-frequency="12h" --resource-group "rg1"
"""

helps['redisenterprise database delete'] = """
    type: command
    short-summary: Delete a single database in a Redis Enterprise cache
    examples:
      - name: Delete a single database in a Redis Enterprise cache.
        text: |-
               az redisenterprise database delete --cluster-name "cache1" --resource-group "rg1"
"""

helps['redisenterprise database export'] = """
    type: command
    short-summary: Export data stored in a Redis Enterprise database
    long-summary: Export data stored in a Redis Enterprise database to a target database file
    examples:
      - name: Export data stored in a Redis Enterprise database to a target database file.
        text: |-
               az redisenterprise database export --cluster-name "cache1" --sas-uri "https://contosostorage.blob.core.w\
indow.net/urlToBlobContainer?sasKeyParameters" --resource-group "rg1"
"""

helps['redisenterprise database import'] = """
    type: command
    short-summary: Import data into a Redis Enterprise database
    long-summary: Import data from a database file into a target Redis Enterprise database
    examples:
      - name: Import data from a database file into a target Redis Enterprise database.
        text: |-
               az redisenterprise database import --cluster-name "cache1" --sas-uri "https://contosostorage.blob.core.w\
indow.net/urltoBlobFile?sasKeyParameters" --resource-group "rg1"
"""

helps['redisenterprise database list-keys'] = """
    type: command
    short-summary: Retrieve all access keys for a Redis Enterprise database
    examples:
      - name: Retrieve all access keys for a Redis Enterprise database.
        text: |-
               az redisenterprise database list-keys --cluster-name "cache1" --resource-group "rg1"
"""

helps['redisenterprise database regenerate-key'] = """
    type: command
    short-summary: Regenerate an access key for a Redis Enterprise database
    examples:
      - name: Regenerate an access key for a Redis Enterprise database.
        text: |-
               az redisenterprise database regenerate-key --cluster-name "cache1" --key-type "Primary" \
--resource-group "rg1"
"""

helps['redisenterprise database wait'] = """
    type: command
    short-summary: Place the CLI in a waiting state until a condition of the Redis Enterprise database is met
    examples:
      - name: Pause executing next line of CLI script until the Redis Enterprise database is successfully created.
        text: |-
               az redisenterprise database wait --cluster-name "cache1" --resource-group "rg1" --created
      - name: Pause executing next line of CLI script until the Redis Enterprise database is successfully updated.
        text: |-
               az redisenterprise database wait --cluster-name "cache1" --resource-group "rg1" --updated
      - name: Pause executing next line of CLI script until the Redis Enterprise database is successfully deleted.
        text: |-
               az redisenterprise database wait --cluster-name "cache1" --resource-group "rg1" --deleted
"""
