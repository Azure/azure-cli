# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
# pylint: disable=unused-argument


# EXAMPLE: /RedisEnterprise/put/RedisEnterpriseCreate
def step_create(test, rg, checks=None):
    if checks is None:
        checks = []
    if test.kwargs.get('no_database') is True:
        test.cmd('az redisenterprise create '
                 '--cluster-name "{cluster}" '
                 '--sku "EnterpriseFlash_F300" '
                 '--capacity 3 '
                 '--tags tag1="value1" '
                 '--zones "1" "2" "3" '
                 '--minimum-tls-version "1.2" '
                 '--no-database '
                 '--resource-group "{rg}"',
                 checks=checks)
    else:
        test.cmd('az redisenterprise create '
                 '--cluster-name "{cluster}" '
                 '--sku "Enterprise_E20" '
                 '--capacity 4 '
                 '--tags tag1="value1" '
                 '--zones "1" "2" "3" '
                 '--minimum-tls-version "1.2" '
                 '--client-protocol "Encrypted" '
                 '--clustering-policy "EnterpriseCluster" '
                 '--eviction-policy "NoEviction" '
                 '--modules name="RedisBloom" args="ERROR_RATE 0.00 INITIAL_SIZE 400" '
                 '--modules name="RedisTimeSeries" args="RETENTION_POLICY 20" '
                 '--modules name="RediSearch" '
                 '--persistence aof-enabled=true aof-frequency="1s" '
                 '--port 10000 '
                 '--resource-group "{rg}"',
                 checks=checks)


# EXAMPLE: /RedisEnterprise/get/RedisEnterpriseGet
def step_show(test, rg, checks=None):
    if checks is None:
        checks = []
    test.cmd('az redisenterprise show '
             '--cluster-name "{cluster}" '
             '--resource-group "{rg}"',
             checks=checks)


# EXAMPLE: /RedisEnterprise/delete/RedisEnterpriseDelete
def step_delete(test, rg, checks=None):
    if checks is None:
        checks = []
    test.cmd('az redisenterprise delete -y '
             '--cluster-name "{cluster}" '
             '--resource-group "{rg}"',
             checks=checks)


# EXAMPLE: /Databases/put/RedisEnterpriseDatabasesCreate
def step_database_create(test, rg, checks=None):
    if checks is None:
        checks = []
    test.cmd('az redisenterprise database create '
             '--cluster-name "{cluster}" '
             '--client-protocol "Plaintext" '
             '--clustering-policy "OSSCluster" '
             '--eviction-policy "AllKeysLRU" '
             '--persistence rdb-enabled=true rdb-frequency="12h" '
             '--port 10000 '
             '--resource-group "{rg}"',
             checks=checks)


# EXAMPLE: /Databases/get/RedisEnterpriseDatabasesGet
def step_database_show(test, rg, checks=None):
    if checks is None:
        checks = []
    test.cmd('az redisenterprise database show '
             '--cluster-name "{cluster}" '
             '--resource-group "{rg}"',
             checks=checks)


# EXAMPLE: /Databases/get/RedisEnterpriseDatabasesListByCluster
def step_database_list(test, rg, checks=None):
    if checks is None:
        checks = []
    test.cmd('az redisenterprise database list '
             '--cluster-name "{cluster}" '
             '--resource-group "{rg}"',
             checks=checks)


# EXAMPLE: /Databases/post/RedisEnterpriseDatabasesListKeys
def step_database_list_keys(test, rg, checks=None):
    if checks is None:
        checks = []
    test.cmd('az redisenterprise database list-keys '
             '--cluster-name "{cluster}" '
             '--resource-group "{rg}"',
             checks=checks)


# EXAMPLE: /Databases/post/RedisEnterpriseDatabasesRegenerateKey
def step_database_regenerate_key(test, rg, checks=None):
    if checks is None:
        checks = []
    test.cmd('az redisenterprise database regenerate-key '
             '--cluster-name "{cluster}" '
             '--key-type "Primary" '
             '--resource-group "{rg}"',
             checks=checks)


# EXAMPLE: /Databases/delete/RedisEnterpriseDatabasesDelete
def step_database_delete(test, rg, checks=None):
    if checks is None:
        checks = []
    test.cmd('az redisenterprise database delete -y '
             '--cluster-name "{cluster}" '
             '--resource-group "{rg}"',
             checks=checks)
