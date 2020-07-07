# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

import os
from glob import glob

from knack.util import CLIError

from .const import COMMAND_MODULE_PREFIX, EXTENSION_PREFIX, ENV_VAR_VIRTUAL_ENV


def extract_module_name(path):

    import re

    _CORE_NAME_REGEX = re.compile(r'azure-cli-(?P<name>[^/\\]+)[/\\]azure[/\\]cli')
    _MOD_NAME_REGEX = re.compile(r'azure-cli[/\\]azure[/\\]cli[/\\]command_modules[/\\](?P<name>[^/\\]+)')
    _EXT_NAME_REGEX = re.compile(r'.*(?P<name>azext_[^/\\]+).*')

    for expression in [_MOD_NAME_REGEX, _CORE_NAME_REGEX, _EXT_NAME_REGEX]:
        match = re.search(expression, path)
        if not match:
            continue
        return match.groupdict().get('name')
    raise CLIError('unexpected error: unable to extract name from path: {}'.format(path))


def get_env_path():
    """ Returns the path to the current virtual environment.

    :returns: Path (str) to the virtual env or None.
    """
    env_path = None
    for item in ENV_VAR_VIRTUAL_ENV:
        env_path = os.environ.get(item)
        if env_path:
            break
    return env_path


def get_azdev_repo_path():
    """ Return the path to the azdev repo root.

    :returns: Path (str) to azdev repo.
    """
    here = os.path.dirname(os.path.realpath(__file__))
    while not os.path.exists(os.path.join(here, '.git')):
        here = os.path.dirname(here)
    return here


def get_cli_repo_path():
    """ Return the path to the Azure CLI repo.

    :returns: Path (str) to Azure CLI repo.
    """
    from configparser import NoSectionError
    from .config import get_azdev_config
    try:
        return get_azdev_config().get('cli', 'repo_path')
    except NoSectionError:
        raise CLIError('Unable to retrieve CLI repo path from config. Please run `azdev setup`.')


def get_ext_repo_paths():
    """ Return the paths to the Azure CLI dev extensions.

    :returns: Path (str) to Azure CLI dev extension repos.
    """
    from configparser import NoSectionError
    from .config import get_azdev_config
    try:
        return get_azdev_config().get('ext', 'repo_paths').split(',')
    except NoSectionError:
        raise CLIError('Unable to retrieve extensions repo path from config. Please run `azdev setup`.')


def find_file(file_name):
    """ Returns the path to a specific file.

    :returns: Path (str) to file or None.
    """
    for path, _, files in os.walk(os.getcwd()):
        if file_name in files:
            return path
    return None


def find_files(root_paths, file_pattern):
    """ Returns the paths to all files that match a given pattern.

    :returns: Paths ([str]) to files matching the given pattern.
    """
    if isinstance(root_paths, str):
        root_paths = [root_paths]
    paths = []
    for root_path in root_paths:
        for path, _, _ in os.walk(root_path):
            pattern = os.path.join(path, file_pattern)
            paths.extend(glob(pattern))
    return paths


def make_dirs(path):
    """ Create directories recursively. """
    import errno
    try:
        os.makedirs(os.path.expanduser(path))
    except OSError as exc:  # Python <= 2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def get_name_index(invert=False, include_whl_extensions=False):
    """ Returns a dictionary containing the long and short names of modules and extensions is {SHORT:LONG} format or
        {LONG:SHORT} format when invert=True. """
    from azure.cli.core.extension import EXTENSIONS_DIR  # pylint: disable=import-error

    table = {}
    cli_repo_path = get_cli_repo_path()
    ext_repo_paths = get_ext_repo_paths()

    # unified azure-cli package (2.0.68 and later)
    paths = os.path.normcase(
        os.path.join(
            cli_repo_path, 'src', 'azure-cli', 'azure', 'cli', 'command_modules', '*', '__init__.py'
        )
    )
    modules_paths = glob(paths)
    core_paths = glob(os.path.normcase(os.path.join(cli_repo_path, 'src', '*', 'setup.py')))
    ext_paths = [x for x in find_files(ext_repo_paths, '*.*-info') if 'site-packages' not in x]
    whl_ext_paths = []
    if include_whl_extensions:
        whl_ext_paths = [x for x in find_files(EXTENSIONS_DIR, '*.*-info') if 'site-packages' not in x]

    def _update_table(paths, key):
        folder = None
        long_name = None
        short_name = None
        for path in paths:
            folder = os.path.dirname(path)
            base_name = os.path.basename(folder)
            # determine long-names
            if key == 'ext':
                short_name = base_name
                for item in os.listdir(folder):
                    if item.startswith(EXTENSION_PREFIX):
                        long_name = item
                        break
            elif base_name.startswith(COMMAND_MODULE_PREFIX):
                long_name = base_name
                short_name = base_name.replace(COMMAND_MODULE_PREFIX, '') or '__main__'
            else:
                short_name = base_name
                long_name = '{}{}'.format(COMMAND_MODULE_PREFIX, base_name)
            if not invert:
                table[short_name] = long_name
            else:
                table[long_name] = short_name

    _update_table(modules_paths, 'mod')
    _update_table(core_paths, 'core')
    _update_table(ext_paths, 'ext')
    _update_table(whl_ext_paths, 'ext')

    return table


# pylint: disable=too-many-statements
def get_path_table(include_only=None, include_whl_extensions=False):
    """ Returns a table containing the long and short names of different modules and extensions and the path to them.
        The structure looks like:
    {
        'core': {
            NAME: PATH,
            ...
        },
        'mod': {
            NAME: PATH,
            ...
        },
        'ext': {
            NAME: PATH,
            ...
        }
    }
    """
    from azure.cli.core.extension import EXTENSIONS_DIR  # pylint: disable=import-error

    # determine whether the call will filter or return all
    if isinstance(include_only, str):
        include_only = [include_only]
    get_all = not include_only

    table = {}
    cli_repo_path = get_cli_repo_path()
    ext_repo_paths = get_ext_repo_paths()

    paths = os.path.normcase(
        os.path.join(
            cli_repo_path, 'src', 'azure-cli', 'azure', 'cli', 'command_modules', '*', '__init__.py'
        )
    )
    modules_paths = glob(paths)
    core_paths = glob(os.path.normcase(os.path.join(cli_repo_path, 'src', '*', 'setup.py')))
    ext_paths = [x for x in find_files(ext_repo_paths, '*.*-info') if 'site-packages' not in x]
    whl_ext_paths = [x for x in find_files(EXTENSIONS_DIR, '*.*-info') if 'site-packages' not in x]

    def _update_table(package_paths, key):
        if key not in table:
            table[key] = {}

        for path in package_paths:
            folder = os.path.dirname(path)
            base_name = os.path.basename(folder)

            if key == 'ext':
                short_name = base_name
                long_name = next((item for item in os.listdir(folder) if item.startswith(EXTENSION_PREFIX)), None)
            else:
                short_name = base_name
                long_name = '{}{}'.format(COMMAND_MODULE_PREFIX, base_name)

            if get_all:
                table[key][long_name if key == 'ext' else short_name] = folder
            elif not include_only:
                return  # nothing left to filter
            else:
                # check and update filter
                if short_name in include_only:
                    include_only.remove(short_name)
                    table[key][short_name] = folder
                if long_name in include_only:
                    # long name takes precedence to ensure path doesn't appear twice
                    include_only.remove(long_name)
                    table[key].pop(short_name, None)
                    table[key][long_name] = folder

    _update_table(modules_paths, 'mod')
    _update_table(core_paths, 'core')
    _update_table(ext_paths, 'ext')
    if include_whl_extensions:
        _update_table(whl_ext_paths, 'ext')

    if include_only:
        whl_extensions = [mod for whl_ext_path in whl_ext_paths for mod in include_only if mod in whl_ext_path]
        if whl_extensions:
            err = 'extension(s): [ {} ] installed from a wheel may need --include-whl-extensions option'.format(
                ', '.join(whl_extensions))
            raise CLIError(err)

        raise CLIError('unrecognized modules: [ {} ]'.format(', '.join(include_only)))

    return table
