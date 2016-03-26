import pip
from six.moves import input #pylint: disable=redefined-builtin

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

@command('components install')
@description(L('Install a component'))
@option('--name -n <name>', L('Name of component to install'), required=True)
@option('--version <version>', L('Component version (otherwise latest)'))
@option('--link -l <url>', L("If a url or path to an html file, then parse \
for links to archives. If a local path or \
file:// url that's a directory,then look for \
archives in the directory listing."))
@option('--private -p', L('Get from the project private PyPI server'))
def install_component(args, unexpected): #pylint: disable=unused-argument
    component_name = args.get('name')
    version = args.get('version')
    link = args.get('link')
    private = args.get('private')
    if not component_name:
        raise IncorrectUsageError(L('Specify a component name.'))
    if link and private:
        raise IncorrectUsageError(L("Specify either link or private. Not both."))
    found = bool([dist for dist in pip.get_installed_distributions(local_only=False)
                  if dist.key==COMPONENT_PREFIX+component_name])
    if found:
        # TODO:: Check for updates
        raise RuntimeError("Component already installed.")
    else:
        version_no = '==' + version if version else ''
        extra_params = []
        if link:
            extra_params = ['--find-links', link]
        elif private:
            extra_params = ['--extra-index-url', 'http://40.112.211.51:8080/', '--trusted-host', '40.112.211.51']
        pip.main(['install', '--quiet', '--isolated', '--disable-pip-version-check',
                  COMPONENT_PREFIX + component_name+version_no] + extra_params)

# @command('components update')
# @description(L('Update a component'))
# @option('--name -n <name>', L('Name of component to install'), required=True)
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
@option('--name -n <name>', L('Name of component to remove'), required=True)
@option('--force -f', L('supress delete confirmation prompt'))
def remove_component(args, unexpected): #pylint: disable=unused-argument
    component_name = args.get('name')
    prompt_for_delete = args.get('force') is None
    if not component_name:
        raise IncorrectUsageError(L('Specify a component name.'))
    found = bool([dist for dist in pip.get_installed_distributions(local_only=False)
                  if dist.key==COMPONENT_PREFIX+component_name])
    if found:
        if prompt_for_delete:
            ans = input("Really delete '{}'? [Y/n] ".format(component_name))
            if not ans or ans[0].lower() != 'y':
                return
        pip.main(['uninstall', '--quiet', '--isolated', '--yes', '--disable-pip-version-check', COMPONENT_PREFIX+component_name])
    else:
        raise RuntimeError(L("Component not installed."))
