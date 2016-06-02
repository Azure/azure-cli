# pylint: disable=line-too-long
from azure.cli.commands.argument_types import CliArgumentType, register_cli_argument
from azure.cli.commands._validators import validate_tag, validate_tags

resource_group_name_type = CliArgumentType(options_list=('--resource-group', '-g'), help='Name of resource group')

name_type = CliArgumentType(options_list=('--name', '-n'), help='the primary resource name')

location_type = CliArgumentType(
    options_list=('--location', '-l'),
    help='Location. Use "az locations get" to get a list of valid locations', metavar='LOCATION')

tags_type = CliArgumentType(
    type=validate_tags,
    help='multiple semicolon separated tags in \'key[=value]\' format. Omit value to clear tags.',
    nargs='?',
    default=''
)

tag_type = CliArgumentType(
    type=validate_tag,
    help='a single tag in \'key[=value]\' format. Omit value to clear tags.',
    nargs='?',
    default=''
)

register_cli_argument('', 'resource_group_name', resource_group_name_type)
register_cli_argument('', 'location', location_type)
