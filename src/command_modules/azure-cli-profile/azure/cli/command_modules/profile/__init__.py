import azure.cli.command_modules.profile.account
import azure.cli.command_modules.profile.login
import azure.cli.command_modules.profile.logout
from azure.cli.command_modules.profile.command_tables import COMMAND_TABLES, generate_command_table

command_table = generate_command_table()
