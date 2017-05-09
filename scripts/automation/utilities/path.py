# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os.path
import glob

from automation.utilities.const import COMMAND_MODULE_PREFIX


def get_repo_root():
    """Returns the path to the source code root directory"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    while not os.path.exists(os.path.join(current_dir, 'CONTRIBUTING.rst')):
        current_dir = os.path.dirname(current_dir)

    return current_dir


def get_all_module_paths():
    """List all core and command modules"""
    return list(get_core_modules_paths()) + list(get_command_modules_paths(include_prefix=True))


def get_command_modules_paths(include_prefix=False):
    for path in glob.glob(get_repo_root() + '/src/command_modules/{}*/setup.py'.format(
            COMMAND_MODULE_PREFIX)):
        folder = os.path.dirname(path)
        name = os.path.basename(folder)
        if not include_prefix:
            name = name[len(COMMAND_MODULE_PREFIX):]
        yield name, folder


def get_command_modules_paths_with_tests():
    return get_module_paths_with_tests(get_command_modules_paths())


def get_core_modules_paths_with_tests():
    return get_module_paths_with_tests(get_core_modules_paths())


def get_core_modules_paths():
    for path in glob.glob(get_repo_root() + '/src/*/setup.py'):
        yield os.path.basename(os.path.dirname(path)), os.path.dirname(path)


def get_module_paths_with_tests(modules):
    for name, path in modules:
        test_folder = os.path.join(path, 'tests')
        if not os.path.exists(test_folder):
            # fallback, will be obsolete eventually when all tests folder are moved to the root of
            # it's module source folder.
            name = name.replace(COMMAND_MODULE_PREFIX, '')
            test_folder = os.path.join(path, 'azure', 'cli', 'command_modules', name, 'tests')
            if not os.path.exists(test_folder):
                test_folder = None

        if test_folder:
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


def filter_user_selected_modules_with_tests(user_input_modules):
    import itertools

    existing_modules = list(itertools.chain(get_core_modules_paths_with_tests(),
                                            get_command_modules_paths_with_tests()))

    if user_input_modules:
        selected_modules = set(user_input_modules)
        extra = selected_modules - set([name for name, _, _ in existing_modules])
        if any(extra):
            print('ERROR: These modules do not exist: {}.'.format(', '.join(extra)))
            return None

        return list((name, module, test) for name, module, test in existing_modules
                    if name in selected_modules)
    else:
        return list((name, module, test) for name, module, test in existing_modules)


if __name__ == '__main__':
    print('Automation utility')
    print('All modules and their paths')

    module_paths = get_all_module_paths()
    template = '  {:' + str(max([len(m) for m, _ in module_paths]) + 2) + '}{}'

    for m, p in module_paths:
        print(template.format(m, p))

    print('Total: {}\n\n'.format(len(module_paths)))

    print('Core modules and their paths')

    module_paths = list(get_core_modules_paths())
    template = '  {:' + str(max([len(m) for m, _ in module_paths]) + 2) + '}{}'

    for m, p in module_paths:
        print(template.format(m, p))

    print('Total: {}\n\n'.format(len(module_paths)))

    print('Command modules and their paths')

    module_paths = list(get_command_modules_paths())
    template = '  {:' + str(max([len(m) for m, _ in module_paths]) + 2) + '}{}'

    for m, p in module_paths:
        print(template.format(m, p))

    print('Total: {}\n\n'.format(len(module_paths)))

    print('Core modules and their paths as well as tests')

    module_paths = list(get_core_modules_paths_with_tests())
    name_len = str(max([len(m) for m, _, _ in module_paths]) + 2)
    template = '  {:' + name_len + '}{}\n  {:' + name_len + '}{}'

    for m, p, t in module_paths:
        print(template.format(m, p, '', t))

    print('Total: {}\n\n'.format(len(module_paths)))

    print('Command modules and their paths as well as tests')

    module_paths = list(get_command_modules_paths_with_tests())
    name_len = str(max([len(m) for m, _, _ in module_paths]) + 2)
    template = '  {:' + name_len + '}{}\n  {:' + name_len + '}{}'

    for m, p, t in module_paths:
        print(template.format(m, p, '', t))

    print('Total: {}\n\n'.format(len(module_paths)))
