# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.arguments import CLIArgumentType

from azure.cli.core.commands.parameters import (
    resource_group_name_type,
    get_enum_type,
    get_three_state_flag)

name_arg_type = CLIArgumentType(metavar='NAME', configured_default='botname', id_part='Name')


# pylint: disable=line-too-long,too-many-statements
def load_arguments(self, _):
    with self.argument_context('bot') as c:
        c.argument('resource_group_name', arg_type=resource_group_name_type)
        c.argument('resource_name', options_list=['--name', '-n'], help='the Resource Name of the bot.', arg_type=name_arg_type)

    with self.argument_context('bot create') as c:
        c.argument('sku_name', options_list=['--sku'], arg_type=get_enum_type(['F0', 'S1']), help='the Sku of the Bot', arg_group='Registration Bot Specific')
        c.argument('kind', options_list=['--kind', '-k'], arg_type=get_enum_type(['registration', 'function', 'webapp']), help='The Kind of the Bot.')
        c.argument('display_name', help='the Display Name of the bot.If not specified, defaults to the name of the bot.', arg_group='Registration Bot Specific')
        c.argument('description', options_list=['--description', '-d'], help='the Description of the bot.', arg_group='Registration Bot Specific')
        c.argument('endpoint', options_list=['-e', '--endpoint'], help='the Messaging Endpoint of the bot.', arg_group='Registration Bot Specific')
        c.argument('msa_app_id', options_list=['--appid'], help='the msa account id to be used with the bot.')
        c.argument('password', options_list=['-p', '--password'], help='the msa password for the bot from developer portal.')
        c.argument('storageAccountName', options_list=['-s', '--storage'], help='Storage Account Name to be used with the bot.If one is not provided, a new account will be created.', arg_group='Web/Function Bot Specific')
        c.argument('tags', help='set of tags to add to the bot.')
        c.argument('language', help='The language to be used to create the bot.', options_list=['--lang'], arg_type=get_enum_type(['Csharp', 'Node']), arg_group='Web/Function Bot Specific')
        c.argument('appInsightsLocation', help='The location for the app insights to be used with the bot.', options_list=['--insights'], arg_group='Web/Function Bot Specific')
        c.argument('version', options_list=['-v', '--version'], help='the bot sdk version to be used to create the bot', arg_type=get_enum_type(['v3', 'v4']), arg_group='Web/Function Bot Specific')

    with self.argument_context('bot publish') as c:
        c.argument('code_dir', options_list=['--code-dir'], help='The root directory from which the code will be uploaded.')

    with self.argument_context('bot download') as c:
        c.argument('file_save_path', options_list=['--save-path'], help='the root directory to which the file should be saved to.')

    with self.argument_context('bot show') as c:
        c.argument('bot_json', options_list=['--msbot'], help='show the output as json compatible with a .bot file', arg_type=get_three_state_flag())

    with self.argument_context('bot prepare-publish') as c:
        c.argument('proj_name', help='name of the start up project file name. Required only for CSharp.')
        c.argument('sln_name', help='name of the start up solution file name. Required only for CSharp.')
        c.argument('code_dir', options_list=['--code-dir'], help='The root directory to which the deployment scripts will be downloaded.')

    with self.argument_context('bot facebook create') as c:
        c.argument('is_disabled', options_list=['--add-disabled'], arg_type=get_three_state_flag(), help='add the channel in a disabled state')
        c.argument('page_id', options_list=['--page-id'], help='page id of the facebook page to be used for the bot.')
        c.argument('app_id', options_list=['--appid'], help='the facebook application id.')
        c.argument('app_secret', options_list=['--secret'], help='the facebook application secret.')
        c.argument('access_token', options_list=['--token'], help='the facebook application access token.')

    with self.argument_context('bot email create') as c:
        c.argument('is_disabled', options_list=['--add-disabled'], arg_type=get_three_state_flag())
        c.argument('email_address', options_list=['--email-address', '-a'], help='the email address for the bot.')
        c.argument('password', options_list=['--password', '-p'], help='the email password for the bot.')

    with self.argument_context('bot msteams create') as c:
        c.argument('is_disabled', options_list=['--add-disabled'], arg_type=get_three_state_flag(), help='add the channel in a disabled state')
        c.argument('enable_calling', help='Enable calling on MsTeams', arg_type=get_three_state_flag())
        c.argument('calling_web_hook', help='The calling web hook to use on MsTeams')

    with self.argument_context('bot skype create') as c:
        c.argument('is_disabled', options_list=['--add-disabled'], arg_type=get_three_state_flag(), help='add the channel in a disabled state')
        c.argument('enable_messaging', help='Enable messaging on Skype', arg_type=get_three_state_flag())
        c.argument('enable_media_cards', help='Enable media cards on Skype', arg_type=get_three_state_flag())
        c.argument('enable_video', help='Enable video on Skype', arg_type=get_three_state_flag())
        c.argument('enable_calling', help='Enable calling on Skype', arg_type=get_three_state_flag())
        c.argument('enable_screen_sharing', help='Enable screen sharing on Skype', arg_type=get_three_state_flag())
        c.argument('enable_groups', help='Enable groups on Skype', arg_type=get_three_state_flag())
        c.argument('groups_mode', help='select groups mode on Skype')
        c.argument('calling_web_hook', help='The calling web hook to use on Skype')

    with self.argument_context('bot kik create') as c:
        c.argument('is_disabled', options_list=['--add-disabled'], arg_type=get_three_state_flag(), help='add the channel in a disabled state')
        c.argument('user_name', options_list=['--user-name', '-u'], help='kik user name')
        c.argument('is_validated', help='Has the user name been validated', arg_type=get_three_state_flag())
        c.argument('api_key', options_list=['--key'], help='the api key for the kik account')

    with self.argument_context('bot webchat create') as c:
        c.argument('is_disabled', options_list=['--add-disabled'], arg_type=get_three_state_flag(), help='add the channel in a disabled state')
        c.argument('site_name', options_list=['-s', '--site-name'], help='name of the webchat channel site')
        c.argument('enable_preview', help='Enable preview features on the chat control', arg_type=get_three_state_flag())

    with self.argument_context('bot directline create') as c:
        c.argument('is_disabled', options_list=['--add-disabled'], arg_type=get_three_state_flag(), help='add the channel in a disabled state')
        c.argument('site_name', options_list=['-s', '--site-name'], help='name of the webchat channel site')
        c.argument('is_v1_disabled', options_list=['--disablev1'], help='Enable v1 channel protocol', arg_type=get_three_state_flag())
        c.argument('is_v3_disabled', options_list=['--disablev3'], help='Enable v3 channel protocol', arg_type=get_three_state_flag())

    with self.argument_context('bot telegram create') as c:
        c.argument('is_disabled', options_list=['--add-disabled'], arg_type=get_three_state_flag())
        c.argument('access_token', help='The access token for the telegram account')
        c.argument('is_validated', help='Has the user name been validated', arg_type=get_three_state_flag())

    with self.argument_context('bot sms create') as c:
        c.argument('is_disabled', options_list=['--add-disabled'], arg_type=get_three_state_flag(), help='add the channel in a disabled state')
        c.argument('account_sid', help='The account sid for the twilio account')
        c.argument('auth_token', help='The token token for the twilio account.')
        c.argument('is_validated', help='Has the user name been validated.', arg_type=get_three_state_flag())
        c.argument('phone', help='the phone number for the twilio account.')

    with self.argument_context('bot slack create') as c:
        c.argument('is_disabled', options_list=['--add-disabled'], arg_type=get_three_state_flag(), help='add the channel in a disabled state')
        c.argument('client_secret', help='The client secret from slack')
        c.argument('client_id', help='The client id from slack')
        c.argument('verification_token', help='The verification token from slack')
        c.argument('landing_page_url', help='The landing page url to redirect to after login')

    with self.argument_context('bot authsetting') as c:
        c.argument('connection_name', options_list=['--setting-name', '-c'], help='name of the oauth connection setting', id_part='child_name_1')

    with self.argument_context('bot authsetting create') as c:
        c.argument('client_id', help='client id associated with the service provider setting')
        c.argument('client_secret', help='client secret associated with the service provider setting')
        c.argument('scopes', help='scopes associated with the service provider setting.The format depends on the service provider.')
        c.argument('service_provider_name', options_list=['--service'], help='name of the service provider. For a list of all service providers, use az bot connection listserviceproviders')
        c.argument('parameters', help='parameter values for Service Provider Parameters. Usage: --parameters key=value key1=value1', nargs='+')

    with self.argument_context('bot authsetting list-providers') as c:
        c.argument('as_raw_settings', options_list=['--as-raw'], help='Output the raw json for each service provider', arg_type=get_three_state_flag())
        c.argument('name', options_list=['--provider-name'], help='service provider name for which to fetch details')

    for channel in ['facebook', 'email', 'msteams', 'skype', 'kik', 'webchat', 'directline', 'telegram', 'sms', 'slack']:
        with self.argument_context('bot {0} show'.format(channel)) as c:
            c.argument('show_secrets', options_list=['--with-secrets'], help='Show secrets in response for the channel', arg_type=get_three_state_flag())
