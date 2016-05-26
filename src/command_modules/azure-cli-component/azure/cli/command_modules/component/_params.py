from azure.cli.commands.argument_types import register_cli_argument, CliArgumentType

# BASIC PARAMETER CONFIGURATION

register_cli_argument('component', 'component_name', CliArgumentType(
    options_list=('--name', '-n'),
    help='Name of component'
))
register_cli_argument('component', 'force', CliArgumentType(
    options_list=('--force', '-f'),
    help='Supress delete confirmation prompt',
    action='store_true'
))
register_cli_argument('component', 'link', CliArgumentType(
    options_list=('--link', '-l'),
    help='If a url or path to an html file, parse for links to archives. If local path or file://'
         'url that\'s a directory, then look for archives in the directory listing.'
))
register_cli_argument('component', 'private', CliArgumentType(
    options_list=('--private', '-p'),
    help='Get from the project PyPI server',
    action='store_true'
))
register_cli_argument('component', 'version', CliArgumentType(
    help='Component version (otherwise latest)'
))
