# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

import glob
from importlib import import_module
import json
import os
import re
from subprocess import CalledProcessError
import sys

from knack.log import get_logger
from knack.util import CLIError

from azdev.utilities import (
    display, output, heading, subheading,
    cmd as raw_cmd, py_cmd, pip_cmd, find_file, IS_WINDOWS,
    ENV_VAR_TEST_LIVE,
    COMMAND_MODULE_PREFIX, EXTENSION_PREFIX,
    make_dirs, get_azdev_config_dir,
    get_path_table, require_virtual_env, get_name_index)
from .pytest_runner import get_test_runner
from .profile_context import ProfileContext, current_profile
from .incremental_strategy import CLIAzureDevOpsContext

logger = get_logger(__name__)


# pylint: disable=too-many-statements
def run_tests(tests, xml_path=None, discover=False, in_series=False,
              run_live=False, profile=None, last_failed=False, pytest_args=None,
              no_exit_first=False,
              git_source=None, git_target=None, git_repo=None,
              cli_ci=False):

    require_virtual_env()

    DEFAULT_RESULT_FILE = 'test_results.xml'
    DEFAULT_RESULT_PATH = os.path.join(get_azdev_config_dir(), DEFAULT_RESULT_FILE)

    heading('Run Tests')

    path_table = get_path_table()

    test_index = _get_test_index(profile or current_profile(), discover)

    if not tests:
        tests = list(path_table['mod'].keys()) + list(path_table['core'].keys()) + list(path_table['ext'].keys())
    if tests == ['CLI']:
        tests = list(path_table['mod'].keys()) + list(path_table['core'].keys())
    elif tests == ['EXT']:
        tests = list(path_table['ext'].keys())

    # filter out tests whose modules haven't changed
    modified_mods = _filter_by_git_diff(tests, test_index, git_source, git_target, git_repo)
    if modified_mods:
        display('\nTest on modules: {}\n'.format(', '.join(modified_mods)))

    if cli_ci is True:
        ctx = CLIAzureDevOpsContext(git_repo, git_source, git_target)
        modified_mods = ctx.filter(test_index)

    # resolve the path at which to dump the XML results
    xml_path = xml_path or DEFAULT_RESULT_PATH
    if not xml_path.endswith('.xml'):
        xml_path = os.path.join(xml_path, DEFAULT_RESULT_FILE)

    # process environment variables
    if run_live:
        logger.warning('RUNNING TESTS LIVE')
        os.environ[ENV_VAR_TEST_LIVE] = 'True'

    def _find_test(index, name):
        name_comps = name.split('.')
        num_comps = len(name_comps)
        key_error = KeyError()

        for i in range(num_comps):
            check_name = '.'.join(name_comps[(-1 - i):])
            try:
                match = index[check_name]
                if check_name != name:
                    logger.info("Test found using just '%s'. The rest of the name was ignored.\n", check_name)
                return match
            except KeyError as ex:
                key_error = ex
                continue
        raise key_error

    # lookup test paths from index
    test_paths = []
    for t in modified_mods:
        try:
            test_path = os.path.normpath(_find_test(test_index, t))
            test_paths.append(test_path)
        except KeyError:
            logger.warning("'%s' not found. If newly added, re-run with --discover", t)
            continue

    exit_code = 0

    # Tests have been collected. Now run them.
    if not test_paths:
        logger.warning('No tests selected to run.')
        sys.exit(exit_code)

    exit_code = 0
    with ProfileContext(profile):
        runner = get_test_runner(parallel=not in_series,
                                 log_path=xml_path,
                                 last_failed=last_failed,
                                 no_exit_first=no_exit_first)
        exit_code = runner(test_paths=test_paths, pytest_args=pytest_args)

    sys.exit(0 if not exit_code else 1)


def _filter_by_git_diff(tests, test_index, git_source, git_target, git_repo):
    from azdev.utilities import diff_branches, extract_module_name
    from azdev.utilities.git_util import summarize_changed_mods

    if not any([git_source, git_target, git_repo]):
        return tests

    if not all([git_target, git_repo]):
        raise CLIError('usage error: [--src NAME]  --tgt NAME --repo PATH')

    files_changed = diff_branches(git_repo, git_target, git_source)
    mods_changed = summarize_changed_mods(files_changed)

    repo_path = str(os.path.abspath(git_repo)).lower()
    to_remove = []
    for key in tests:
        test_path = test_index.get(key, None)
        if test_path and test_path.lower().startswith(repo_path):
            mod_name = extract_module_name(test_path)
            if next((x for x in mods_changed if mod_name in x), None):
                # has changed, so do not filter out
                continue
        # in not in the repo or has not changed, filter out
        to_remove.append(key)
    # remove the unchanged modules
    tests = [t for t in tests if t not in to_remove]

    logger.info('Filtered out: %s', to_remove)

    return tests


def _discover_module_tests(mod_name, mod_data):

    # get the list of test files in each module
    total_tests = 0
    total_files = 0
    logger.info('Mod: %s', mod_name)
    try:
        contents = os.listdir(mod_data['filepath'])
        test_files = {
            x[:-len('.py')]: {} for x in contents if x.startswith('test_') and x.endswith('.py')
        }
        total_files = len(test_files)
    except (OSError, IOError) as ex:
        err_string = str(ex)
        if 'system cannot find the path' in err_string or 'No such file or directory' in err_string:
            # skip modules that don't have tests
            logger.info('  No test files found.')
            return None
        raise

    for file_name in test_files:
        mod_data['files'][file_name] = {}
        test_file_path = mod_data['base_path'] + '.' + file_name
        try:
            module = import_module(test_file_path)
        except ImportError as ex:
            logger.info('    %s', ex)
            continue
        module_dict = module.__dict__
        possible_test_classes = {x: y for x, y in module_dict.items() if not x.startswith('_')}
        for class_name, class_def in possible_test_classes.items():
            try:
                class_dict = class_def.__dict__
            except AttributeError:
                # skip non-class symbols in files like constants, imported methods, etc.
                continue
            if class_dict.get('__module__') == test_file_path:
                tests = [x for x in class_def.__dict__ if x.startswith('test_')]
                if tests:
                    mod_data['files'][file_name][class_name] = tests
                total_tests += len(tests)
    logger.info('  %s tests found in %s files.', total_tests, total_files)
    return mod_data


# pylint: disable=too-many-statements, too-many-locals
def _discover_tests(profile):
    """ Builds an index of tests so that the user can simply supply the name they wish to test instead of the
        full path.
    """
    profile_split = profile.split('-')
    profile_namespace = '_'.join([profile_split[-1]] + profile_split[:-1])

    heading('Discovering Tests')

    path_table = get_path_table()
    core_modules = path_table['core'].items()
    command_modules = path_table['mod'].items()
    extensions = path_table['ext'].items()
    inverse_name_table = get_name_index(invert=True)

    module_data = {}

    logger.info('\nCore Modules: %s', ', '.join([name for name, _ in core_modules]))
    for mod_name, mod_path in core_modules:
        file_path = mod_path
        for comp in mod_name.split('-'):
            file_path = os.path.join(file_path, comp)

        mod_data = {
            'alt_name': 'main' if mod_name == 'azure-cli' else mod_name.replace(COMMAND_MODULE_PREFIX, ''),
            'filepath': os.path.join(file_path, 'tests'),
            'base_path': '{}.tests'.format(mod_name).replace('-', '.'),
            'files': {}
        }
        tests = _discover_module_tests(mod_name, mod_data)
        if tests:
            module_data[mod_name] = tests

    logger.info('\nCommand Modules: %s', ', '.join([name for name, _ in command_modules]))
    for mod_name, mod_path in command_modules:
        mod_data = {
            # Modules don't technically have azure-cli-foo moniker anymore, but preserving
            # for consistency.
            'alt_name': '{}{}'.format(COMMAND_MODULE_PREFIX, mod_name),
            'filepath': os.path.join(
                mod_path, 'tests', profile_namespace),
            'base_path': 'azure.cli.command_modules.{}.tests.{}'.format(mod_name, profile_namespace),
            'files': {}
        }
        tests = _discover_module_tests(mod_name, mod_data)
        if tests:
            module_data[mod_name] = tests

    logger.info('\nExtensions: %s', ', '.join([name for name, _ in extensions]))
    for mod_name, mod_path in extensions:
        glob_pattern = os.path.normcase(os.path.join('{}*'.format(EXTENSION_PREFIX)))
        try:
            file_path = glob.glob(os.path.join(mod_path, glob_pattern))[0]
        except IndexError:
            logger.debug("No extension found at: %s", os.path.join(mod_path, glob_pattern))
            continue
        import_name = os.path.basename(file_path)
        mod_data = {
            'alt_name': inverse_name_table[mod_name],
            'filepath': os.path.join(file_path, 'tests', profile_namespace),
            'base_path': '{}.tests.{}'.format(import_name, profile_namespace),
            'files': {}
        }
        tests = _discover_module_tests(import_name, mod_data)
        if tests:
            module_data[mod_name] = tests

    test_index = {}
    conflicted_keys = []

    def add_to_index(key, path):
        from azdev.utilities import extract_module_name

        key = key or mod_name
        if key in test_index:
            if key not in conflicted_keys:
                conflicted_keys.append(key)
            mod1 = extract_module_name(path)
            mod2 = extract_module_name(test_index[key])
            if mod1 != mod2:
                # resolve conflicted keys by prefixing with the module name and a dot (.)
                logger.warning("'%s' exists in both '%s' and '%s'. Resolve using `%s.%s` or `%s.%s`",
                               key, mod1, mod2, mod1, key, mod2, key)
                test_index['{}.{}'.format(mod1, key)] = path
                test_index['{}.{}'.format(mod2, key)] = test_index[key]
            else:
                logger.error("'%s' exists twice in the '%s' module. "
                             "Please rename one or both and re-run --discover.", key, mod1)
        else:
            test_index[key] = path

    # build the index
    for mod_name, mod_data in module_data.items():
        # don't add empty mods to the index
        if not mod_data:
            continue

        mod_path = mod_data['filepath']
        for file_name, file_data in mod_data['files'].items():
            file_path = os.path.join(mod_path, file_name) + '.py'
            for class_name, test_list in file_data.items():
                for test_name in test_list:
                    test_path = '{}::{}::{}'.format(file_path, class_name, test_name)
                    add_to_index(test_name, test_path)
                class_path = '{}::{}'.format(file_path, class_name)
                add_to_index(class_name, class_path)
            add_to_index(file_name, file_path)
        add_to_index(mod_name, mod_path)
        add_to_index(mod_data['alt_name'], mod_path)

    # remove the conflicted keys since they would arbitrarily point to a random implementation
    for key in conflicted_keys:
        del test_index[key]

    return test_index


def _get_test_index(profile, discover):
    config_dir = get_azdev_config_dir()
    test_index_dir = os.path.join(config_dir, 'test_index')
    make_dirs(test_index_dir)
    test_index_path = os.path.join(test_index_dir, '{}.json'.format(profile))
    test_index = {}
    if discover:
        test_index = _discover_tests(profile)
        with open(test_index_path, 'w') as f:
            f.write(json.dumps(test_index))
        display('\ntest index updated: {}'.format(test_index_path))
    elif os.path.isfile(test_index_path):
        with open(test_index_path, 'r') as f:
            test_index = json.loads(''.join(f.readlines()))
        display('\ntest index found: {}'.format(test_index_path))
    else:
        test_index = _discover_tests(profile)
        with open(test_index_path, 'w') as f:
            f.write(json.dumps(test_index))
        display('\ntest index created: {}'.format(test_index_path))
    return test_index
