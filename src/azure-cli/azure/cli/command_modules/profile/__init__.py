# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core import AzCommandsLoader
from azure.cli.core.commands import CliCommandType
from azure.cli.core.commands.parameters import get_enum_type

from azure.cli.command_modules.profile._format import transform_account_list
import azure.cli.command_modules.profile._help  # pylint: disable=unused-import

from ._validators import validate_tenant

cloud_resource_types = ["oss-rdbms", "arm", "aad-graph", "ms-graph", "batch", "media", "data-lake"]


class ProfileCommandsLoader(AzCommandsLoader):

    def __init__(self, cli_ctx=None):
        super(ProfileCommandsLoader, self).__init__(cli_ctx=cli_ctx)

    def load_command_table(self, args):

        profile_custom = CliCommandType(
            operations_tmpl='azure.cli.command_modules.profile.custom#{}'
        )

        with self.command_group('', profile_custom) as g:
            g.command('login', 'login')
            g.command('logout', 'logout')
            g.command('self-test', 'check_cli', deprecate_info=g.deprecate(hide=True))

        with self.command_group('account', profile_custom) as g:
            g.command('list', 'list_subscriptions', table_transformer=transform_account_list)
            g.command('set', 'set_active_subscription')
            g.show_command('show', 'show_subscription')
            g.command('clear', 'account_clear')
            g.command('list-locations', 'list_locations')
            g.command('get-access-token', 'get_access_token')

        return self.command_table

    # pylint: disable=line-too-long
    def load_arguments(self, command):
        from azure.cli.core.api import get_subscription_id_list

        with self.argument_context('login') as c:
            c.argument('password', options_list=['--password', '-p'], help="Credentials like user password, or for a service principal, provide client secret or a pem file with key and public certificate. Will prompt if not given.")
            c.argument('service_principal', action='store_true', help='The credential representing a service principal.')
            c.argument('username', options_list=['--username', '-u'], help='user name, service principal, or managed service identity ID')
            c.argument('tenant', options_list=['--tenant', '-t'], help='The AAD tenant, must provide when using service principals.', validator=validate_tenant)
            c.argument('allow_no_subscriptions', action='store_true', help="Support access tenants without subscriptions. It's uncommon but useful to run tenant level commands, such as 'az ad'")
            c.ignore('_subscription')  # hide the global subscription parameter
            c.argument('identity', options_list=('-i', '--identity'), action='store_true', help="Log in using the Virtual Machine's identity", arg_group='Managed Service Identity')
            c.argument('identity_port', type=int, help="the port to retrieve tokens for login. Default: 50342", arg_group='Managed Service Identity')
            c.argument('use_device_code', action='store_true',
                       help="Use CLI's old authentication flow based on device code. CLI will also use this if it can't launch a browser in your behalf, e.g. in remote SSH or Cloud Shell")
            c.argument('use_cert_sn_issuer', action='store_true', help='used with a service principal configured with Subject Name and Issuer Authentication in order to support automatic certificate rolls')
            c.argument('scopes', options_list=['--scope'], nargs='+', help='Used in the /authorize request. It can cover only one static resource.')
            c.argument('client_assertion', options_list=['--federated-token'], help='Federated token that can be used for OIDC token exchange.')

        with self.argument_context('logout') as c:
            c.argument('username', help='account user, if missing, logout the current active account')
            c.ignore('_subscription')  # hide the global subscription parameter

        with self.argument_context('account') as c:
            c.argument('subscription', options_list=['--subscription', '-s', '--name', '-n'], arg_group='', help='Name or ID of subscription.', completer=get_subscription_id_list)
            c.ignore('_subscription')

        with self.argument_context('account list') as c:
            c.argument('all', help="List all subscriptions from all clouds, rather than just 'Enabled' ones", action='store_true')
            c.argument('refresh', help="retrieve up-to-date subscriptions from server", action='store_true')
            c.ignore('_subscription')  # hide the global subscription parameter

        with self.argument_context('account get-access-token') as c:
            c.argument('resource_type', get_enum_type(cloud_resource_types), options_list=['--resource-type'], arg_group='', help='Type of well-known resource.')
            c.argument('resource', options_list=['--resource'], help='Azure resource endpoints in AAD v1.0.')
            c.argument('scopes', options_list=['--scope'], nargs='*', help='Space-separated AAD scopes in AAD v2.0. Default to Azure Resource Manager.')
            c.argument('tenant', options_list=['--tenant', '-t'], help='Tenant ID for which the token is acquired. Only available for user and service principal account, not for MSI or Cloud Shell account')
            c.argument('show_claims', help='Show the decoded claims of the access token.')


COMMAND_LOADER_CLS = ProfileCommandsLoader
