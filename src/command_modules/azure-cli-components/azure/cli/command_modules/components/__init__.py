from __future__ import print_function
import pip
from six.moves import input #pylint: disable=redefined-builtin

from azure.cli.parser import IncorrectUsageError
from azure.cli.commands import CommandTable, COMMON_PARAMETERS
from azure.cli._locale import L

COMPONENT_PREFIX = 'azure-cli-'

command_table = CommandTable()

@command_table.command('components list')
@command_table.description(L('List the installed components.'))
def list_components(args, unexpected): #pylint: disable=unused-argument
    components = sorted(["%s (%s)" % (dist.key.replace(COMPONENT_PREFIX, ''), dist.version)
                         for dist in pip.get_installed_distributions(local_only=True)
                         if dist.key.startswith(COMPONENT_PREFIX)])
    print('\n'.join(components))

def _install_or_update(component_name, version, link, private, upgrade=False):
    if not component_name:
        raise IncorrectUsageError(L('Specify a component name.'))
    found = bool([dist for dist in pip.get_installed_distributions(local_only=True)
                  if dist.key == COMPONENT_PREFIX+component_name])
    if found and not upgrade:
        raise RuntimeError("Component already installed.")
    else:
        version_no = '==' + version if version else ''
        options = ['--quiet', '--isolated', '--disable-pip-version-check']
        if upgrade:
            options.append('--upgrade')
        pkg_index_options = []
        if link:
            pkg_index_options += ['--find-links', link]
        if private:
            pkg_index_options += ['--extra-index-url', 'http://40.112.211.51:8080/',
                                  '--trusted-host', '40.112.211.51']
        pip.main(['install'] + options + [COMPONENT_PREFIX + component_name+version_no]
                 + pkg_index_options)

@command_table.command('components install')
@command_table.description(L('Install a component'))
@command_table.option('--name -n <name>', help=L('Name of component to install'), required=True)
@command_table.option('--version <version>', help=L('Component version (otherwise latest)'))
@command_table.option('--link -l <url>', help=L("If a url or path to an html file, then parse \
for links to archives. If a local path or \
file:// url that's a directory,then look for \
archives in the directory listing."))
@command_table.option('--private -p', help=L('Get from the project private PyPI server'))
def install_component(args, unexpected): #pylint: disable=unused-argument
    _install_or_update(args.get('name'), args.get('version'), args.get('link'),
                       args.get('private'), upgrade=False)

@command_table.command('components update')
@command_table.description(L('Update a component'))
@command_table.option('--name -n <name>', help=L('Name of component to install'), required=True)
@command_table.option('--link -l <url>', help=L("If a url or path to an html file, then parse \
for links to archives. If a local path or \
file:// url that's a directory,then look for \
archives in the directory listing."))
@command_table.option('--private -p', help=L('Get from the project private PyPI server'))
def update_component(args, unexpected): #pylint: disable=unused-argument
    _install_or_update(args.get('name'), None, args.get('link'), args.get('private'), upgrade=True)

@command_table.command('components update all')
@command_table.description(L('Update all components'))
@command_table.option('--link -l <url>', help=L("If a url or path to an html file, then parse \
for links to archives. If a local path or \
file:// url that's a directory,then look for \
archives in the directory listing."))
@command_table.option('--private -p', help=L('Get from the project private PyPI server'))
def update_all_components(args, unexpected): #pylint: disable=unused-argument
    component_names = [dist.key.replace(COMPONENT_PREFIX, '')
                       for dist in pip.get_installed_distributions(local_only=True)
                       if dist.key.startswith(COMPONENT_PREFIX)]
    for component_name in component_names:
        _install_or_update(component_name, None, args.get('link'),
                           args.get('private'), upgrade=True)

@command_table.command('components remove')
@command_table.description(L('Remove a component'))
@command_table.option('--name -n <name>', help=L('Name of component to remove'), required=True)
@command_table.option('--force -f', help=L('supress delete confirmation prompt'))
def remove_component(args, unexpected): #pylint: disable=unused-argument
    component_name = args.get('name')
    prompt_for_delete = args.get('force') is None
    if not component_name:
        raise IncorrectUsageError(L('Specify a component name.'))
    found = bool([dist for dist in pip.get_installed_distributions(local_only=True)
                  if dist.key == COMPONENT_PREFIX+component_name])
    if found:
        if prompt_for_delete:
            ans = input("Really delete '{}'? [Y/n] ".format(component_name))
            if not ans or ans[0].lower() != 'y':
                return
        pip.main(['uninstall', '--quiet', '--isolated', '--yes',
                  '--disable-pip-version-check', COMPONENT_PREFIX+component_name])
    else:
        raise RuntimeError(L("Component not installed."))
