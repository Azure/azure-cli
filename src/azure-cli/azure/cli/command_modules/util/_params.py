# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


# pylint: disable=line-too-long
def load_arguments(self, _):
    from azure.cli.core.commands.parameters import get_enum_type, get_three_state_flag
    from azure.cli.core.style import Theme

    with self.argument_context('rest') as c:
        c.argument('method', options_list=['--method', '-m'],
                   arg_type=get_enum_type(['head', 'get', 'put', 'post', 'delete', 'options', 'patch'], default='get'),
                   help='HTTP request method')
        c.argument('url', options_list=['--url', '--uri', '-u'],
                   help='Request URL. If it doesn\'t start with a host, '
                        'CLI assumes it as an Azure resource ID and prefixes it with the ARM endpoint of the current '
                        'cloud shown by `az cloud show --query endpoints.resourceManager`. Common token '
                        '{subscriptionId} will be replaced with the current subscription ID specified by `az account '
                        'set`')
        c.argument('headers', nargs='+',
                   help="Space-separated headers in KEY=VALUE format or JSON string. Use @{file} to load from a file")
        c.argument('uri_parameters', options_list=['--uri-parameters', '--url-parameters'], nargs='+',
                   help='Query parameters in the URL. Space-separated queries in KEY=VALUE format or JSON string. '
                        'Use @{file} to load from a file')
        c.argument('skip_authorization_header', action='store_true', help='Do not auto-append Authorization header')
        c.argument('body', options_list=['--body', '-b'],
                   help='Request body. Use @{file} to load from a file. For quoting issues in different terminals, '
                        'see https://github.com/Azure/azure-cli/blob/dev/doc/use_cli_effectively.md#quoting-issues')
        c.argument('output_file', help='save response payload to a file')
        c.argument('resource',
                   help='Resource url for which CLI should acquire a token from AAD in order to access '
                        'the service. The token will be placed in the Authorization header. By default, '
                        'CLI can figure this out based on --url argument, unless you use ones not in the list '
                        'of "az cloud show --query endpoints"')

    with self.argument_context('upgrade') as c:
        c.argument('update_all', options_list=['--all'], arg_type=get_three_state_flag(), help='Enable updating extensions as well.', default='true')
        c.argument('yes', options_list=['--yes', '-y'], action='store_true', help='Do not prompt for checking release notes.')

    with self.argument_context('demo style') as c:
        c.argument('theme', arg_type=get_enum_type(Theme),
                   help='The theme to format styled text. If unspecified, the default theme is used.')
