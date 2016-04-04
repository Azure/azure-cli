COMMAND_TABLES = []
from azure.cli.commands import CommandTable
import azure.cli.command_modules.profile.account
import azure.cli.command_modules.profile.login
import azure.cli.command_modules.profile.logout

# Combine the command tables in this package to produce a single command table.
command_table = CommandTable()
for ct in COMMAND_TABLES:
    command_table.update(ct)
