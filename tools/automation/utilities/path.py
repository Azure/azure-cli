# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import glob

from automation.utilities.const import COMMAND_MODULE_PREFIX, EXTENSIONS_MOD_PREFIX


def get_repo_root():
    """Returns the path to the source code root directory"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    while not os.path.exists(os.path.join(current_dir, 'CONTRIBUTING.rst')):
        current_dir = os.path.dirname(current_dir)

    return current_dir


def get_all_module_paths():
    """List all core and command modules"""
    return list(get_core_modules_paths()) + list(get_command_modules_paths(include_prefix=True))


def get_config_dir():
    """ Returns the users Azure directory. """
    return os.getenv('AZURE_CONFIG_DIR', None) or os.path.expanduser(os.path.join('~', '.azure'))


def get_extension_dir():
    """ Returns the extensions directory. """
    custom_dir = os.environ.get('AZURE_EXTENSION_DIR')
    return os.path.expanduser(custom_dir) if custom_dir else os.path.join(get_config_dir(), 'cliextensions')


def get_extensions_paths(include_prefix=False):
    glob_pattern = os.path.normcase('/*/{}*'.format(EXTENSIONS_MOD_PREFIX))
    for path in glob.glob(get_extension_dir() + glob_pattern):
        name = os.path.basename(path)
        if not include_prefix:
            name = name[len(EXTENSIONS_MOD_PREFIX):]
        yield name, path


def get_command_modules_paths(include_prefix=False):
    glob_pattern = os.path.normcase('/src/command_modules/{}*/setup.py'.format(COMMAND_MODULE_PREFIX))
    for path in glob.glob(get_repo_root() + glob_pattern):
        folder = os.path.dirname(path)
        name = os.path.basename(folder)
        if not include_prefix:
            name = name[len(COMMAND_MODULE_PREFIX):]
        yield name, folder


def get_command_modules_paths_with_tests(profile):
    return get_module_paths_with_tests(get_command_modules_paths(), profile)


def get_core_modules_paths_with_tests(profile):
    if profile == 'latest':
        for name, path in get_core_modules_paths():
            for root, dirs, files in os.walk(path):
                if os.path.basename(root) == 'tests':
                    if name == 'azure-cli-core':
                        name = 'core'
                    yield name, path, root


def get_core_modules_paths():
    for path in glob.glob(get_repo_root() + os.path.normcase('/src/*/setup.py')):
        yield os.path.basename(os.path.dirname(path)), os.path.dirname(path)


def get_module_paths_with_tests(modules, profile):
    for name, path in modules:
        name = name.replace(COMMAND_MODULE_PREFIX, '')
        test_folder = os.path.join(path, 'azure', 'cli', 'command_modules', name, 'tests', profile)
        if os.path.exists(test_folder):
            yield name, path, test_folder


def make_dirs(path):
    """Create a directories recursively"""
    import errno
    try:
        os.makedirs(path)
    except OSError as exc:  # Python <= 2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def get_test_results_dir(with_timestamp=None, prefix=None):
    """Returns the folder where test results should be saved to. If the folder doesn't exist,
    it will be created."""
    result = os.path.join(get_repo_root(), 'test_results')

    if isinstance(with_timestamp, bool):
        from datetime import datetime
        with_timestamp = datetime.now()

    if with_timestamp:
        if prefix:
            result = os.path.join(result, with_timestamp.strftime(prefix + '_%Y%m%d_%H%M%S'))
        else:
            result = os.path.join(result, with_timestamp.strftime('%Y%m%d_%H%M%S'))

    if not os.path.exists(result):
        make_dirs(result)

    if not os.path.exists(result) or not os.path.isdir(result):
        raise Exception('Failed to create test result dir {}'.format(result))

    return result


def filter_blacklisted_modules(*black_list_modules):
    """Returns the paths to the modules except those in the black list."""
    import itertools

    existing_modules = list(itertools.chain(get_core_modules_paths(),
                                            get_command_modules_paths()))
    black_list_modules = set(black_list_modules)
    return list((name, path) for name, path in existing_modules if name not in black_list_modules)


def filter_user_selected_modules(user_input_modules):
    import itertools

    existing_modules = list(itertools.chain(get_core_modules_paths(),
                                            get_command_modules_paths()))

    if user_input_modules:
        selected_modules = set(user_input_modules)
        extra = selected_modules - set([name for name, _ in existing_modules])
        if any(extra):
            print('ERROR: These modules do not exist: {}.'.format(', '.join(extra)))
            return None

        return list((name, module) for name, module in existing_modules
                    if name in selected_modules)
    else:
        return list((name, module) for name, module in existing_modules)


def filter_user_selected_modules_with_tests(user_input_modules=None, profile=None):
    import itertools

    existing_modules = list(itertools.chain(get_core_modules_paths_with_tests(profile),
                                            get_command_modules_paths_with_tests(profile)))

    if user_input_modules is not None:
        selected_modules = set(user_input_modules)
        extra = selected_modules - set([name for name, _, _ in existing_modules])
        # don't count extensions as extras
        extra = [x for x in extra if not x.startswith('azext_')]
        if any(extra):
            print('ERROR: These modules do not exist: {}.'.format(', '.join(extra)))
            return None

        return list((name, module, test) for name, module, test in existing_modules
                    if name in selected_modules)
    else:
        return list((name, module, test) for name, module, test in existing_modules)
