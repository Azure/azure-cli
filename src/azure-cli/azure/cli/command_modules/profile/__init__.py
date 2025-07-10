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
        super().__init__(cli_ctx=cli_ctx)

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
            g.command('get-access-token', 'get_access_token')

        return self.command_table

    def load_arguments(self, command):
        from azure.cli.core.api import get_subscription_id_list

        with self.argument_context('login') as c:
            c.argument('username', options_list=['--username', '-u'],
                       help='User name or service principal client ID.')
            c.argument('password', options_list=['--password', '-p'],
                       help='User password or service principal secret. Will prompt if not given.')
            c.argument('tenant', options_list=['--tenant', '-t'], validator=validate_tenant,
                       help='The Microsoft Entra tenant, must be provided when using a service principal.')
            c.argument('scopes', options_list=['--scope'], nargs='+',
                       help='Used in the /authorize request. It can cover only one static resource.')
            c.argument('allow_no_subscriptions', action='store_true',
                       help="Support accessing tenants without subscriptions. It's useful to run "
                            "tenant-level commands, such as 'az ad'.")
            c.argument('claims_challenge',
                       help="Base64-encoded claims challenge requested by a resource API in the "
                            "WWW-Authenticate header.")
            c.ignore('_subscription')  # hide the global subscription parameter

            # Device code flow
            c.argument('use_device_code', action='store_true',
                       help="Use device code flow. Azure CLI will also use this if it can't launch a browser, "
                            "e.g. in remote SSH or Cloud Shell.")

            # Service principal
            c.argument('service_principal', action='store_true',
                       help='Log in with a service principal.')
            c.argument('certificate', help='PEM file with key and public certificate.')
            c.argument('use_cert_sn_issuer', action='store_true',
                       help='Use Subject Name + Issuer (SN+I) authentication in order to support automatic '
                            'certificate rolls.')
            c.argument('client_assertion', options_list=['--federated-token'],
                       help='Federated token that can be used for OIDC token exchange.')

            # Managed identity
            c.argument('identity', options_list=('-i', '--identity'), action='store_true',
                       help="Log in using managed identity", arg_group='Managed Identity')
            c.argument('client_id',
                       help="Client ID of the user-assigned managed identity", arg_group='Managed Identity')
            c.argument('object_id',
                       help="Object ID of the user-assigned managed identity", arg_group='Managed Identity')
            c.argument('resource_id',
                       help="Resource ID of the user-assigned managed identity", arg_group='Managed Identity')

        with self.argument_context('logout') as c:
            c.argument('username', help='account user, if missing, logout the current active account')
            c.ignore('_subscription')  # hide the global subscription parameter

        with self.argument_context('account') as c:
            c.argument('subscription', options_list=['--subscription', '-s', '--name', '-n'],
                       completer=get_subscription_id_list, help='Name or ID of subscription.')
            c.ignore('_subscription')

        with self.argument_context('account list') as c:
            c.argument('all', action='store_true',
                       help="List all subscriptions from all clouds, including subscriptions that are not 'Enabled'.")
            c.argument('refresh', help="retrieve up-to-date subscriptions from server", action='store_true')
            c.ignore('_subscription')  # hide the global subscription parameter

        with self.argument_context('account get-access-token') as c:
            c.argument('resource_type', get_enum_type(cloud_resource_types), options_list=['--resource-type'],
                       help='Type of well-known resource.')
            c.argument('resource', options_list=['--resource'],
                       help='Azure resource endpoints in Microsoft Entra v1.0.')
            c.argument('scopes', options_list=['--scope'], nargs='*',
                       help='Space-separated scopes in Microsoft Entra v2.0. Default to Azure Resource Manager.')
            c.argument('tenant', options_list=['--tenant', '-t'],
                       help='Tenant ID for which the token is acquired. Only available for user and service principal '
                            'account, not for managed identity or Cloud Shell account')


COMMAND_LOADER_CLS = ProfileCommandsLoader
