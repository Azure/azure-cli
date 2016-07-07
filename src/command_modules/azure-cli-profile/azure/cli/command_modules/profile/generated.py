from __future__ import print_function

from azure.cli.commands import cli_command

from .custom import (login,
                     logout,
                     list_location,
                     list_subscriptions,
                     set_active_subscription,
                     account_clear,
                     create_service_principal,
                     reset_service_principal_credential)

cli_command('login', login)
cli_command('logout', logout)

cli_command('account list', list_subscriptions)
cli_command('account set', set_active_subscription)
cli_command('account clear', account_clear)
cli_command('account list-location', list_location)

cli_command('account create-sp', create_service_principal)
cli_command('account reset-sp-credentials', reset_service_principal_credential)

