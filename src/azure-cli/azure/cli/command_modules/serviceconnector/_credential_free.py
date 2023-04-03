# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import struct
import sys
from knack.log import get_logger
from msrestazure.tools import parse_resource_id
from azure.cli.core.azclierror import (
    AzureConnectionError,
    ValidationError,
    CLIInternalError
)
from azure.cli.core.extension.operations import _install_deps_for_psycopg2, _run_pip
from azure.cli.core._profile import Profile
from ._utils import run_cli_cmd, generate_random_string, is_packaged_installed, get_object_id_of_current_user
from ._resource_config import (
    RESOURCE,
    AUTH_TYPE
)
from ._validators import (
    get_source_resource_name,
    get_target_resource_name,
)

logger = get_logger(__name__)

AUTHTYPES = {
    AUTH_TYPE.SystemIdentity: 'systemAssignedIdentity',
    AUTH_TYPE.UserIdentity: 'userAssignedIdentity',
    AUTH_TYPE.ServicePrincipalSecret: 'servicePrincipalSecret',
    AUTH_TYPE.UserAccount: 'userAccount',
}


# pylint: disable=line-too-long, consider-using-f-string
# For db(mysqlFlex/psql/psqlFlex/sql) linker with AAD auth type, it's passwordless connection and requires extension installation
def is_passwordless_command(cmd, auth_info):
    # return if connection is not for db mi
    if auth_info['auth_type'] not in {AUTHTYPES[AUTH_TYPE.SystemIdentity], AUTHTYPES[AUTH_TYPE.UserAccount], AUTHTYPES[AUTH_TYPE.ServicePrincipalSecret], AUTHTYPES[AUTH_TYPE.UserIdentity]}:
        return False
    source_type = get_source_resource_name(cmd)
    target_type = get_target_resource_name(cmd)
    if source_type not in {RESOURCE.WebApp, RESOURCE.ContainerApp, RESOURCE.SpringCloud, RESOURCE.SpringCloudDeprecated, RESOURCE.Local}:
        return False
    if target_type not in {RESOURCE.Sql, RESOURCE.Postgres, RESOURCE.PostgresFlexible, RESOURCE.MysqlFlexible}:
        return False
    return True
