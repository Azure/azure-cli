# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.arguments import CLIArgumentType

from azure.cli.core.commands.parameters import (
    resource_group_name_type,
    get_enum_type,
    get_three_state_flag,
    tags_type)

name_arg_type = CLIArgumentType(metavar='NAME', configured_default='botname', id_part='Name')


# pylint: disable=line-too-long,too-many-statements
def load_arguments(self, _):
    with self.argument_context('bot') as c:
        c.argument('resource_group_name', arg_type=resource_group_name_type)
        c.argument('resource_name', options_list=['--name', '-n'], help='The resource name of the bot.', arg_type=name_arg_type)

    with self.argument_context('bot create') as c:
        c.argument('sku_name', options_list=['--sku'], arg_type=get_enum_type(['F0', 'S1']), help='The Sku of the bot.', arg_group='Registration bot Specific')
        c.argument('kind', options_list=['--kind', '-k'], arg_type=get_enum_type(['registration', 'function', 'webapp']), help='The kind of the bot.')
        c.argument('display_name', help='The display name of the bot. If not specified, defaults to the name of the bot.', arg_group='Registration bot Specific')
        c.argument('description', options_list=['--description', '-d'], help='The description of the bot.', arg_group='Registration bot Specific')
        c.argument('endpoint', options_list=['-e', '--endpoint'], help='The messaging endpoint of the bot.', arg_group='Registration bot Specific')
        c.argument('msa_app_id', options_list=['--appid'], help='The Microsoft account ID (MSA ID) to be used with the bot.')
        c.argument('password', options_list=['-p', '--password'], help='The Microsoft account (MSA) password for the bot.')
        c.argument('storageAccountName', options_list=['-s', '--storage'], help='Storage account name to be used with the bot. If not provided, a new account will be created.', arg_group='Web/Function bot Specific')
        c.argument('tags', arg_type=tags_type)
        c.argument('language', help='The language to be used to create the bot.', options_list=['--lang'], arg_type=get_enum_type(['Csharp', 'Node']), arg_group='Web/Function bot Specific')
        c.argument('appInsightsLocation', help='The location for the app insights to be used with the bot.', options_list=['--insights-location'], arg_group='Web/Function bot Specific',
                   arg_type=get_enum_type(['South Central US', 'East US', 'West US 2', 'North Europe', 'West Europe', 'Southeast Asia']))
        c.argument('version', options_list=['-v', '--version'], help='The Microsoft Bot Builder SDK version to be used to create the bot', arg_type=get_enum_type(['v3', 'v4']), arg_group='Web/Function bot Specific')

    with self.argument_context('bot publish') as c:
        c.argument('code_dir', options_list=['--code-dir'], help='The directory to upload bot code from.')

    with self.argument_context('bot download') as c:
        c.argument('file_save_path', options_list=['--save-path'], help='The directory to download bot code to.')

    with self.argument_context('bot show') as c:
        c.argument('bot_json', options_list=['--msbot'], help='Show the output as JSON compatible with a .bot file.', arg_type=get_three_state_flag())

    with self.argument_context('bot prepare-publish') as c:
        c.argument('proj_name', help='Name of the start up project file name. Required only for C#.')
        c.argument('sln_name', help='Name of the start up solution file name. Required only for C#.')
        c.argument('code_dir', options_list=['--code-dir'], help='The directory to download deployment scripts to.')

    with self.argument_context('bot facebook create') as c:
        c.argument('is_disabled', options_list=['--add-disabled'], arg_type=get_three_state_flag(), help='Add the channel in a disabled state')
        c.argument('page_id', options_list=['--page-id'], help='Page ID of the Facebook page to be used for the bot.')
        c.argument('app_id', options_list=['--appid'], help='The Facebook application id.')
        c.argument('app_secret', options_list=['--secret'], help='The Facebook application secret.')
        c.argument('access_token', options_list=['--token'], help='The Facebook application access token.')

    with self.argument_context('bot email create') as c:
        c.argument('is_disabled', options_list=['--add-disabled'], arg_type=get_three_state_flag(), help='Add the channel in a disabled state')
        c.argument('email_address', options_list=['--email-address', '-a'], help='The email address for the bot.')
        c.argument('password', options_list=['--password', '-p'], help='The email password for the bot.')

    with self.argument_context('bot msteams create') as c:
        c.argument('is_disabled', options_list=['--add-disabled'], arg_type=get_three_state_flag(), help='Add the channel in a disabled state.')
        c.argument('enable_calling', help='Enable calling on Microsoft Teams.', arg_type=get_three_state_flag())
        c.argument('calling_web_hook', help='The calling web hook to use on Microsoft Teams.')

    with self.argument_context('bot skype create') as c:
        c.argument('is_disabled', options_list=['--add-disabled'], arg_type=get_three_state_flag(), help='Add the channel in a disabled state.')
        c.argument('enable_messaging', help='Enable messaging on Skype.', arg_type=get_three_state_flag())
        c.argument('enable_media_cards', help='Enable media cards on Skype.', arg_type=get_three_state_flag())
        c.argument('enable_video', help='Enable video on Skype.', arg_type=get_three_state_flag())
        c.argument('enable_calling', help='Enable calling on Skype.', arg_type=get_three_state_flag())
        c.argument('enable_screen_sharing', help='Enable screen sharing on Skype.', arg_type=get_three_state_flag())
        c.argument('enable_groups', help='Enable groups on Skype.', arg_type=get_three_state_flag())
        c.argument('groups_mode', help='select groups mode on Skype.')
        c.argument('calling_web_hook', help='The calling web hook to use on Skype.')

    with self.argument_context('bot kik create') as c:
        c.argument('is_disabled', options_list=['--add-disabled'], arg_type=get_three_state_flag(), help='Add the channel in a disabled state.')
        c.argument('user_name', options_list=['--user-name', '-u'], help='Kik user name.')
        c.argument('is_validated', help='Whether or not the Kik account has been validated for use with the bot.', arg_type=get_three_state_flag())
        c.argument('api_key', options_list=['--key'], help='The API key for the Kik account.')

    with self.argument_context('bot webchat create') as c:
        c.argument('is_disabled', options_list=['--add-disabled'], arg_type=get_three_state_flag(), help='Add the channel in a disabled state.')
        c.argument('site_name', options_list=['-s', '--site-name'], help='Name of the Webchat channel site.')
        c.argument('enable_preview', help='Enable preview features on the chat control.', arg_type=get_three_state_flag())

    with self.argument_context('bot directline create') as c:
        c.argument('is_disabled', options_list=['--add-disabled'], arg_type=get_three_state_flag(), help='Add the channel in a disabled state.')
        c.argument('site_name', options_list=['-s', '--site-name'], help='Name of the Directline channel site.')
        c.argument('is_v1_disabled', options_list=['--disablev1'], help='If true, v1 protocol will be disabled on the channel', arg_type=get_three_state_flag())
        c.argument('is_v3_disabled', options_list=['--disablev3'], help='If true, v3 protocol will be disabled on the channel.', arg_type=get_three_state_flag())

    with self.argument_context('bot telegram create') as c:
        c.argument('is_disabled', options_list=['--add-disabled'], arg_type=get_three_state_flag(), help='Add the channel in a disabled state.')
        c.argument('access_token', help='The access token for the Telegram account.')
        c.argument('is_validated', help='Whether or not the Telegram account has been validated for use with the bot.', arg_type=get_three_state_flag())

    with self.argument_context('bot sms create') as c:
        c.argument('is_disabled', options_list=['--add-disabled'], arg_type=get_three_state_flag(), help='Add the channel in a disabled state.')
        c.argument('account_sid', help='The account SID for the Twilio account.')
        c.argument('auth_token', help='The token token for the Twilio account.')
        c.argument('is_validated', help='Whether or not the Twilio account has been validated for use with the bot.', arg_type=get_three_state_flag())
        c.argument('phone', help='The phone number for the Twilio account.')

    with self.argument_context('bot slack create') as c:
        c.argument('is_disabled', options_list=['--add-disabled'], arg_type=get_three_state_flag(), help='Add the channel in a disabled state.')
        c.argument('client_secret', help='The client secret from Slack.')
        c.argument('client_id', help='The client ID from Slack.')
        c.argument('verification_token', help='The verification token from Slack.')
        c.argument('landing_page_url', help='The landing page url to redirect to after login.')

    with self.argument_context('bot authsetting') as c:
        c.argument('connection_name', options_list=['--setting-name', '-c'], help='Name of the oauth connection setting.', id_part='child_name_1')

    with self.argument_context('bot authsetting create') as c:
        c.argument('client_id', help='Client ID associated with the service provider setting.')
        c.argument('client_secret', help='Client secret associated with the service provider setting.')
        c.argument('scopes', options_list=['--provider-scope-string'], help='The scope string associated with the service provider setting.The string should be delimited as needed for the service provider.')
        c.argument('service_provider_name', options_list=['--service'], help='Name of the service provider. For a list of all service providers, use `az bot connection listserviceproviders`.')
        c.argument('parameters', help='Parameter values for service provider parameters. Usage: --parameters key=value key1=value1.', nargs='+')

    with self.argument_context('bot authsetting list-providers') as c:
        c.argument('as_raw_settings', options_list=['--as-raw'], help='Output the raw json for each service provider.', arg_type=get_three_state_flag())
        c.argument('name', options_list=['--provider-name'], help='Service provider name for which to fetch details.')

    for channel in ['facebook', 'email', 'msteams', 'skype', 'kik', 'webchat', 'directline', 'telegram', 'sms', 'slack']:
        with self.argument_context('bot {0} show'.format(channel)) as c:
            c.argument('show_secrets', options_list=['--with-secrets'], help='Show secrets in response for the channel.', arg_type=get_three_state_flag())
