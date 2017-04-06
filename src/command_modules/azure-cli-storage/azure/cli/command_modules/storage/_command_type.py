# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import create_command, command_table
from azure.cli.core._config import az_config
from azure.cli.core.commands.client_factory import get_mgmt_service_client

def query_account_key(account_name):
    from azure.mgmt.storage import StorageManagementClient
    scf = get_mgmt_service_client(StorageManagementClient)
    acc = next((x for x in scf.storage_accounts.list() if x.name == account_name), None)
    if acc:
        from azure.cli.core.commands.arm import parse_resource_id
        rg = parse_resource_id(acc.id)['resource_group']
        return scf.storage_accounts.list_keys(rg, account_name).keys[0].value  # pylint: disable=no-member
    else:
        raise ValueError("Storage account '{}' not found.".format(account_name))


def validate_client_parameters(namespace):
    """ Retrieves storage connection parameters from environment variables and parses out
    connection string into account name and key """
    from azure.cli.core.commands.validators import validate_key_value_pairs

    n = namespace

    if not n.connection_string:
        n.connection_string = az_config.get('storage', 'connection_string', None)

    # if connection string supplied or in environment variables, extract account key and name
    if n.connection_string:
        conn_dict = validate_key_value_pairs(n.connection_string)
        n.account_name = conn_dict['AccountName']
        n.account_key = conn_dict['AccountKey']

    # otherwise, simply try to retrieve the remaining variables from environment variables
    if not n.account_name:
        n.account_name = az_config.get('storage', 'account', None)
    if not n.account_key:
        n.account_key = az_config.get('storage', 'key', None)
    if not n.sas_token:
        n.sas_token = az_config.get('storage', 'sas_token', None)

    # strip the '?' from sas token. the portal and command line are returns sas token in different
    # forms
    if n.sas_token:
        n.sas_token = n.sas_token.lstrip('?')

    # if account name is specified but no key, attempt to query
    if n.account_name and not n.account_key and not n.sas_token:
        n.account_key = query_account_key(n.account_name)


def cli_storage_data_plane_command(name, operation, client_factory,  # pylint: disable=too-many-arguments
                                   transform=None, table_transformer=None, exception_handler=None):
    """ Registers an Azure CLI Storage Data Plane command. These commands always include the
    four parameters which can be used to obtain a storage client: account-name, account-key,
    connection-string, and sas-token. """
    command = create_command(__name__, name, operation, transform, table_transformer,
                             client_factory, exception_handler=exception_handler)
    # add parameters required to create a storage client
    group_name = 'Storage Account'
    command.add_argument('account_name', '--account-name', required=False, default=None,
                         arg_group=group_name,
                         help='Storage account name. Must be used in conjunction with either '
                         'storage account key or a SAS token. Environment variable: '
                         'AZURE_STORAGE_ACCOUNT')
    command.add_argument('account_key', '--account-key', required=False, default=None,
                         arg_group=group_name,
                         help='Storage account key. Must be used in conjunction with storage '
                         'account name. Environment variable: '
                         'AZURE_STORAGE_KEY')
    command.add_argument('connection_string', '--connection-string', required=False, default=None,
                         validator=validate_client_parameters, arg_group=group_name,
                         help='Storage account connection string. Environment variable: '
                         'AZURE_STORAGE_CONNECTION_STRING')
    command.add_argument('sas_token', '--sas-token', required=False, default=None,
                         arg_group=group_name,
                         help='A Shared Access Signature (SAS). Must be used in conjunction with '
                         'storage account name. Environment variable: '
                         'AZURE_STORAGE_SAS_TOKEN')
    command_table[command.name] = command
