import azure.cli.command_modules.profile.account #pylint: disable=unused-import
import azure.cli.command_modules.profile.login #pylint: disable=unused-import
import azure.cli.command_modules.profile.logout #pylint: disable=unused-import
from azure.cli.command_modules.profile.command_tables import generate_command_table

command_table = generate_command_table()
