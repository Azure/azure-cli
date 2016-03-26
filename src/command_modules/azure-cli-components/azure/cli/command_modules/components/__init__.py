import pip
from azure.cli.commands import command, description, option
from azure.cli._locale import L
from azure.cli._argparse import IncorrectUsageError

COMPONENT_PREFIX = 'azure-cli-'

# TODO:: Support installing/removing of a specific version

@command('components list')
@description(L('List the installed components.'))
def list_components(args, unexpected): #pylint: disable=unused-argument
    components = sorted(["%s (%s)" % (dist.key.replace(COMPONENT_PREFIX, ''), dist.version)
                   for dist in pip.get_installed_distributions(local_only=False)
                   if dist.key.startswith(COMPONENT_PREFIX)])
    print('\n'.join(components))

# @command('components check')
# @description(L('Check a component for an update'))
# @option('--name -n <name>')
# def install_component(args, unexpected): #pylint: disable=unused-argument
#     component_name = args.get('name')
#     if not component_name:
#         # Show all
#         pip.main(['list', '--pre', '--outdated', '--isolated',
#         '--trusted-host', '40.112.211.51',
#         '--extra-index-url', 'http://40.112.211.51:8080/'])
#     else:
#         try:
#             __import__('azure.cli.command_modules.'+component_name+'.__main__')
#             # Check for updates
#             pip.main(['list', '--pre', '--outdated', '--isolated',
#             '--trusted-host', '40.112.211.51',
#             '--find-links', 'http://40.112.211.51:8080/simple/azure-cli-'+component_name])
#         except ImportError:
#             raise RuntimeError("Component not installed.")

# @command('components install')
# @description(L('Install a component'))
# @option('--name -n <name>', required=True)
# @option('--version -v <version>')
# def install_component(args, unexpected): #pylint: disable=unused-argument
#     component_name = args.get('name')
#     if not component_name:
#         raise RuntimeError("Specify a component name.")
#     try:
#         __import__('azure.cli.command_modules.'+component_name+'.__main__')
#         # Check for updates
#         pip.main(['list', '--pre', '--outdated', '--isolated',
#         '--trusted-host', '40.112.211.51',
#         '--find-links', 'http://40.112.211.51:8080/simple/azure-cli-'+component_name])
#         raise RuntimeError("Component already installed.")
#     except ImportError:
#         version_no = '=='+args.get('version') if args.get('version') else ''
#         pip.main(['install', '--quiet', '--isolated', '--disable-pip-version-check',
#                   'azure-cli-'+component_name+version_no,
#         '--extra-index-url', 'http://40.112.211.51:8080/', '--trusted-host', '40.112.211.51'])

# @command('components update')
# @description(L('Update a component'))
# @option('--name -n <name>', required=True)
# def update_component(args, unexpected): #pylint: disable=unused-argument
#     component_name = args.get('name')
#     if not component_name:
#         raise RuntimeError("Specify a component name.")
#     try:
#         __import__('azure.cli.command_modules.'+component_name+'.__main__')
#         pip.main(['install', '--quiet', '--isolated', '--disable-pip-version-check',
#                   '--upgrade', 'azure-cli-'+component_name,
#         '--extra-index-url', 'http://40.112.211.51:8080/', '--trusted-host', '40.112.211.51'])
#     except ImportError:
#         raise RuntimeError("Component not installed.")

@command('components remove')
@description(L('Remove a component'))
@option('--name -n <name>', required=True)
def remove_component(args, unexpected): #pylint: disable=unused-argument
    component_name = args.get('name')
    if not component_name:
        raise IncorrectUsageError(L('Specify a component name.'))
    found = [dist for dist in pip.get_installed_distributions(local_only=False)
            if dist.key==COMPONENT_PREFIX+component_name]
    if found:
        pip.main(['uninstall', '--quiet', '--isolated', '--yes', '--disable-pip-version-check', COMPONENT_PREFIX+component_name])
    else:
        raise RuntimeError(L("Component not installed."))
