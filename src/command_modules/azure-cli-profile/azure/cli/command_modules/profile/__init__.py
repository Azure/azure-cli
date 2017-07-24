# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core import AzCommandsLoader

from azure.cli.command_modules.profile.custom import get_subscription_id_list
from azure.cli.command_modules.profile._format import transform_account_list
import azure.cli.command_modules.profile._help  # pylint: disable=unused-import


class ProfileCommandsLoader(AzCommandsLoader):

    def load_command_table(self, args):
        super(ProfileCommandsLoader, self).load_command_table(args)
        profile_custom = 'azure.cli.command_modules.profile.custom#'

        self.cli_command(__name__, 'login', profile_custom + 'login')
        self.cli_command(__name__, 'logout', profile_custom + 'logout')
        self.cli_command(__name__, 'account list', profile_custom + 'list_subscriptions', table_transformer=transform_account_list)
        self.cli_command(__name__, 'account set', profile_custom + 'set_active_subscription')
        self.cli_command(__name__, 'account show', profile_custom + 'show_subscription')
        self.cli_command(__name__, 'account clear', profile_custom + 'account_clear')
        self.cli_command(__name__, 'account list-locations', profile_custom + 'list_locations')
        self.cli_command(__name__, 'account get-access-token', profile_custom + 'get_access_token')
        return self.command_table

    def load_arguments(self, command):
        self.register_cli_argument('login', 'password', options_list=('--password', '-p'), help="Credentials like user password, or for a service principal, provide client secret or a pem file with key and public certificate. Will prompt if not given.")
        self.register_cli_argument('login', 'service_principal', action='store_true', help='The credential representing a service principal.')
        self.register_cli_argument('login', 'username', options_list=('--username', '-u'), help='Organization id or service principal')
        self.register_cli_argument('login', 'tenant', options_list=('--tenant', '-t'), help='The AAD tenant, must provide when using service principals.')
        self.register_cli_argument('login', 'allow_no_subscriptions', action='store_true', help="Support access tenants without subscriptions. It's uncommon but useful to run tenant level commands, such as 'az ad'")

        self.register_cli_argument('logout', 'username', help='account user, if missing, logout the current active account')

        self.register_cli_argument('account', 'subscription', options_list=('--subscription', '-s'), help='Name or ID of subscription.', completer=get_subscription_id_list)
        self.register_cli_argument('account list', 'all', help="List all subscriptions, rather just 'Enabled' ones", action='store_true')
        self.register_cli_argument('account show', 'show_auth_for_sdk', options_list=('--sdk-auth',), action='store_true', help='output result in compatible with Azure SDK auth file')
        super(ProfileCommandsLoader, self).load_arguments(command)
