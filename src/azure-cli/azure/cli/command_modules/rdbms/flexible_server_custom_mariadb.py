# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=unused-argument, line-too-long

import uuid
from msrestazure.azure_exceptions import CloudError
from msrestazure.tools import resource_id, is_valid_resource_id, parse_resource_id  # pylint: disable=import-error
from knack.log import get_logger
from azure.cli.core.commands.client_factory import get_subscription_id
from azure.cli.core.util import CLIError, sdk_no_wait
from azure.mgmt.rdbms.mariadb.operations._servers_operations import ServersOperations as MariaDBServersOperations
from ._client_factory import get_mariadb_management_client

SKU_TIER_MAP = {'Basic': 'b', 'GeneralPurpose': 'gp', 'MemoryOptimized': 'mo'}
logger = get_logger(__name__)

# Meru commands for flexible server

def _flexible_server_create(cmd, client, resource_group_name, server_name, sku_name,
                   location=None, no_wait=False, administrator_login=None, administrator_login_password=None, backup_retention=None,
                   geo_redundant_backup=None, ssl_enforcement=None, storage_mb=None, tags=None, version=None, auto_grow='Enabled',
                   assign_identity=False, public_network_access=None, infrastructure_encryption=None, minimal_tls_version=None):
    from azure.mgmt.rdbms import mariadb
    parameters = mariadb.models.ServerForCreate(
        sku=mariadb.models.Sku(name=sku_name),
        properties=mariadb.models.ServerPropertiesForDefaultCreate(
            administrator_login=administrator_login,
            administrator_login_password=administrator_login_password,
            version=version,
            ssl_enforcement=ssl_enforcement,
            public_network_access=public_network_access,
            storage_profile=mariadb.models.StorageProfile(
                backup_retention_days=backup_retention,
                geo_redundant_backup=geo_redundant_backup,
                storage_mb=storage_mb,
                storage_autogrow=auto_grow)),
        location=location,
        tags=tags)
    return client.create(resource_group_name, server_name, parameters)