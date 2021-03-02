# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.style import print_styled_text, Style
from azure.cli.core.decorators import suppress_all_exceptions


def _get_default_account_text(accounts):
    """Return the type (tenant or subscription) and display text for the default account.

      - For tenant account, only show the tenant ID.
      - For subscription account, if name can uniquely identify the account, only show the name;
        Otherwise, show both name and ID.
    """
    account = next(s for s in accounts if s['isDefault'] is True)
    account_name = account['name']
    account_id = account['id']

    # Tenant account
    from azure.cli.core._profile import _TENANT_LEVEL_ACCOUNT_NAME
    if account_name == _TENANT_LEVEL_ACCOUNT_NAME:
        return "tenant", account_id

    # Subscription account
    # Check if name can uniquely identity the subscription
    accounts_with_name = [a for a in accounts if a['name'] == account_name]
    if len(accounts_with_name) == 1:
        # For unique name, only show the name
        account_text = account_name
    else:
        # If more than 1 accounts have the same name, also show ID
        account_text = '{} ({})'.format(account_name, account_id)

    return 'subscription', account_text


@suppress_all_exceptions()
def login_hinter(cli_ctx, result):  # pylint: disable=unused-argument
    account_type, account_text = _get_default_account_text(result.raw_result)

    command_placeholder = '{:44s}'
    selected_sub = [
        (Style.PRIMARY, 'Your default {} is '.format(account_type)),
        (Style.IMPORTANT, account_text),
    ]
    print_styled_text(selected_sub)
    print_styled_text()

    # TRY
    try_commands = [
        (Style.PRIMARY, 'TRY\n'),
        (Style.PRIMARY, command_placeholder.format('az upgrade')),
        (Style.SECONDARY, 'Upgrade to the latest CLI version in tool\n'),
        (Style.PRIMARY, command_placeholder.format('az account set --subscription <name or id>')),
        (Style.SECONDARY, 'Set your default subscription account\n'),
        (Style.PRIMARY, command_placeholder.format('az config set output=table')),
        (Style.SECONDARY, 'Set your default output to be in table format\n')
    ]
    print_styled_text(try_commands)


@suppress_all_exceptions()
def demo_hint_hinter(cli_ctx, result):  # pylint: disable=unused-argument
    result = result.raw_result
    key_placeholder = '{:>25s}'  # right alignment, 25 width
    command_placeholder = '{:40s}'
    projection = [
        (Style.PRIMARY, 'The hinter can parse the output to show a "projection" of the output, like\n\n'),
        (Style.PRIMARY, key_placeholder.format('Subscription name: ')),
        (Style.IMPORTANT, result['name']),
        (Style.PRIMARY, '\n'),
        (Style.PRIMARY, key_placeholder.format('Subscription ID: ')),
        (Style.IMPORTANT, result['id']),
        (Style.PRIMARY, '\n'),
        (Style.PRIMARY, key_placeholder.format('User: ')),
        (Style.IMPORTANT, result['user']['name']),
    ]
    print_styled_text(projection)
    print_styled_text()

    # TRY
    try_commands = [
        (Style.PRIMARY, 'TRY\n'),
        (Style.PRIMARY, command_placeholder.format('az upgrade')),
        (Style.SECONDARY, 'Upgrade to the latest CLI version in tool\n'),
        (Style.PRIMARY, command_placeholder.format('az account set -s <sub_id or sub_name>')),
        (Style.SECONDARY, 'Set your default subscription account\n'),
        (Style.PRIMARY, command_placeholder.format('az config set output=table')),
        (Style.SECONDARY, 'Set your default output to be in table format\n'),
        (Style.PRIMARY, command_placeholder.format('az feedback')),
        (Style.SECONDARY, 'File us your latest issue encountered\n'),
        (Style.PRIMARY, command_placeholder.format('az next')),
        (Style.SECONDARY, 'Get some ideas on next steps\n'),
    ]
    print_styled_text(try_commands)

    hyperlink = [
        (Style.PRIMARY, 'You may also show a hyperlink for more detail: '),
        (Style.HYPERLINK, 'https://docs.microsoft.com/cli/azure/'),
    ]
    print_styled_text(hyperlink)
