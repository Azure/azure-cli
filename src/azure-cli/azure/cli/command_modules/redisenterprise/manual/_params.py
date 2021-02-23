# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
# pylint: disable=too-many-lines
# pylint: disable=too-many-statements

from azure.cli.core.commands.parameters import (
    get_enum_type
)
from ..action import (
    AddPersistence,
    AddModules
)


def load_arguments(self, _):

    with self.argument_context('redisenterprise create') as c:
        # Update help
        c.argument('sku', arg_type=get_enum_type(['Enterprise_E10', 'Enterprise_E20', 'Enterprise_E50',
                                                  'Enterprise_E100', 'EnterpriseFlash_F300', 'EnterpriseFlash_F700',
                                                  'EnterpriseFlash_F1500']), help='The type of RedisEnterprise cluster '
                   'to deploy.')
        c.argument('minimum_tls_version', arg_type=get_enum_type(['1.0', '1.1', '1.2']), help='The minimum TLS version '
                   'for the cluster to support.')
        # Add database create arguments
        c.argument('client_protocol', arg_type=get_enum_type(['Encrypted', 'Plaintext']), help='Specifies whether '
                   'redis clients can connect using TLS-encrypted or plaintext redis protocols. Default is '
                   'TLS-encrypted.')
        c.argument('port', type=int, help='TCP port of the database endpoint. Specified at create time. Defaults to an '
                   'available port.')
        c.argument('clustering_policy', arg_type=get_enum_type(['EnterpriseCluster', 'OSSCluster']), help='Clustering '
                   'policy - default is OSSCluster. Specified at create time.')
        c.argument('eviction_policy', arg_type=get_enum_type(['AllKeysLFU', 'AllKeysLRU', 'AllKeysRandom',
                                                              'VolatileLRU', 'VolatileLFU', 'VolatileTTL',
                                                              'VolatileRandom', 'NoEviction']), help='Redis eviction '
                   'policy - default is VolatileLRU')
        c.argument('persistence', action=AddPersistence, nargs='+', help='Persistence settings', is_preview=True)
        c.argument('modules', action=AddModules, nargs='+', help='Optional set of redis modules to enable in this '
                   'database - modules can only be added at creation time.')
        # Add new argument
        c.argument('no_database', action='store_true', help='Advanced. Do not automatically create a '
                   'default database. Warning: the cache will not be usable until you create a database.')

    with self.argument_context('redisenterprise update') as c:
        # Update help
        c.argument('sku', arg_type=get_enum_type(['Enterprise_E10', 'Enterprise_E20', 'Enterprise_E50',
                                                  'Enterprise_E100', 'EnterpriseFlash_F300', 'EnterpriseFlash_F700',
                                                  'EnterpriseFlash_F1500']), help='The type of RedisEnterprise cluster '
                   'to deploy.')
        c.argument('minimum_tls_version', arg_type=get_enum_type(['1.0', '1.1', '1.2']), help='The minimum TLS version '
                   'for the cluster to support.')

    with self.argument_context('redisenterprise database update') as c:
        # Update help
        c.argument('client_protocol', arg_type=get_enum_type(['Encrypted', 'Plaintext']), help='Specifies whether '
                   'redis clients can connect using TLS-encrypted or plaintext redis protocols.')
        c.argument('eviction_policy', arg_type=get_enum_type(['AllKeysLFU', 'AllKeysLRU', 'AllKeysRandom',
                                                              'VolatileLRU', 'VolatileLFU', 'VolatileTTL',
                                                              'VolatileRandom', 'NoEviction']), help='Redis eviction '
                   'policy.')
