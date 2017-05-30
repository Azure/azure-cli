# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import _get_cli_argument
from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.core.commands.parameters import ignore_type
from azure.cli.core.sdk.util import ParametersContext

# CLIENT FACTORIES

RM_URI_OVERRIDE = 'AZURE_CLI_RDBMS_RM_URI'
SUB_ID_OVERRIDE = 'AZURE_CLI_RDBMS_SUB_ID'
CLIENT_ID = 'AZURE_CLIENT_ID'
TENANT_ID = 'AZURE_TENANT_ID'
CLIENT_SECRET = 'AZURE_CLIENT_SECRET'


def get_mysql_management_client(_):
    from os import getenv
    from azure.mgmt.rdbms.mysql import MySQLManagementClient

    # Allow overriding resource manager URI using environment variable
    # for testing purposes. Subscription id is also determined by environment
    # variable.
    rm_uri_override = getenv(RM_URI_OVERRIDE)
    if rm_uri_override:
        client_id = getenv(CLIENT_ID)
        if client_id:
            from azure.common.credentials import ServicePrincipalCredentials
            credentials = ServicePrincipalCredentials(
                client_id=client_id,
                secret=getenv(CLIENT_SECRET),
                tenant=getenv(TENANT_ID))
        else:
            from msrest.authentication import Authentication
            credentials = Authentication()

        return MySQLManagementClient(
            subscription_id=getenv(SUB_ID_OVERRIDE),
            base_url=rm_uri_override,
            credentials=credentials)
    else:
        # Normal production scenario.
        return get_mgmt_service_client(MySQLManagementClient)


def get_postgresql_management_client(_):
    from os import getenv
    from azure.mgmt.rdbms.postgresql import PostgreSQLManagementClient

    # Allow overriding resource manager URI using environment variable
    # for testing purposes. Subscription id is also determined by environment
    # variable.
    rm_uri_override = getenv(RM_URI_OVERRIDE)
    if rm_uri_override:
        client_id = getenv(CLIENT_ID)
        if client_id:
            from azure.common.credentials import ServicePrincipalCredentials
            credentials = ServicePrincipalCredentials(
                client_id=client_id,
                secret=getenv(CLIENT_SECRET),
                tenant=getenv(TENANT_ID))
        else:
            from msrest.authentication import Authentication
            credentials = Authentication()

        return PostgreSQLManagementClient(
            subscription_id=getenv(SUB_ID_OVERRIDE),
            base_url=rm_uri_override,
            credentials=credentials)
    else:
        # Normal production scenario.
        return get_mgmt_service_client(PostgreSQLManagementClient)


class PolyParametersContext(ParametersContext):
    def __init__(self, command):
        super(PolyParametersContext, self).__init__(command)
        self.validators = []

    def expand(self, argument_name, model_type, group_name=None, patches=None):
        super(PolyParametersContext, self).expand(argument_name, model_type, group_name, patches)

        # Remove the validator and store it into a list
        arg = _get_cli_argument(self._commmand, argument_name)
        self.validators.append(arg.settings['validator'])
        if argument_name == 'parameters':
            from .validators import get_combined_validator
            self.argument(argument_name,
                          arg_type=ignore_type,
                          validator=get_combined_validator(self.validators))
        else:
            self.argument(argument_name, arg_type=ignore_type, validator=None)
