# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import sys
import argparse
import json
import re
import shlex
from subprocess import check_output, CalledProcessError

from automation.utilities.display import display, output
from automation.utilities.path import filter_user_selected_modules_with_tests, get_config_dir


IS_WINDOWS = sys.platform.lower() in ['windows', 'win32']
TEST_INDEX_FORMAT = 'testIndex_{}.json'


def _separator_line():
    print('-' * 100)


def _extract_module_name(path):
    _CORE_NAME_REGEX = re.compile(r'azure-cli-(?P<name>[^/\\]+)[/\\]azure[/\\]cli')
    _MOD_NAME_REGEX = re.compile(r'azure-cli[/\\]azure[/\\]cli[/\\]command_modules[/\\](?P<name>[^/\\]+)')
    _EXT_NAME_REGEX = re.compile(r'.*(?P<name>azext_[^/\\]+).*')

    for expression in [_MOD_NAME_REGEX, _CORE_NAME_REGEX, _EXT_NAME_REGEX]:
        match = re.search(expression, path)
        if not match:
            continue
        return match.groupdict().get('name')
    raise ValueError('unexpected error: unable to extract name from path: {}'.format(path))


def _extract_modified_files(target_branch=os.environ.get('ADO_PULL_REQUEST_TARGET_BRANCH')):
    ado_raw_env_replacement = '$(System.PullRequest.TargetBranch)'

    if target_branch is None or target_branch == ado_raw_env_replacement:
        # in ADO env but not in PR stage or want to run full test

        # dummy file name src/azure-cli-core/azure/cli/core/__init__.py
        return [os.path.join('src', 'azure-cli-core', 'azure', 'cli', 'core', '__init__.py')]
    else:
        qualified_target_branch = 'origin/{}'.format(target_branch)

    cmd_tpl = 'git --no-pager diff --name-only --diff-filter=ACMRT {} -- src/'
    cmd = cmd_tpl.format(qualified_target_branch)

    modified_files = check_output(cmd, shell=True).decode('utf-8').split('\n')
    modified_files = [f for f in modified_files if len(f) > 0]

    _separator_line()
    if modified_files:
        print('modified files in src/ :', '\n'.join(modified_files))
    else:
        print('no modified files in src/, no need to run automation test')

    return modified_files


def _extract_top_level_modified_modules():
    modified_modules = set()

    modified_files = _extract_modified_files()

    for file_path in modified_files:
        try:
            mod = _extract_module_name(file_path)
            modified_modules.add(mod)
        except ValueError:
            continue

    _separator_line()
    if modified_modules:
        print('related top level modules:', list(modified_modules))
    else:
        print('no related top level modules modified, no need to run automation test')

    return modified_modules


def extract_module_name(path):
    mod_name_regex = re.compile(r'azure[/\\]cli[/\\]([^/\\]+)')
    ext_name_regex = re.compile(r'.*(azext_[^/\\]+).*')

    try:
        return re.search(mod_name_regex, path).group(1)
    except AttributeError:
        return  re.search(ext_name_regex, path).group(1)


def execute(args):
    from .main import run_tests

    validate_usage(args)
    current_profile = get_current_profile(args)
    test_index = get_test_index(args)
    modules = []

    if args.ci:
        # CI Mode runs specific modules
        output('Running in CI Mode')
        selected_modules = [('All modules', 'azure.cli', 'azure.cli'),
                            ('CLI Linter', 'automation.cli_linter', 'automation.cli_linter')]

        modified_modules = _extract_top_level_modified_modules()
        if any(base_mod in modified_modules for base_mod in ['core', 'testsdk', 'telemetry']):
            pass    # if modified modules contains those 3 modules, run all tests
        else:
            test_paths = set()
            for mod in modified_modules:
                try:
                    test_paths.add(os.path.normpath(test_index[mod]))
                except KeyError:
                    display("no tests found in module: {}".format(mod))
            args.tests = test_paths

            selected_modules = []
    elif not (args.tests or args.src_file):
        # Default is to run with modules (possibly via environment variable)
        if os.environ.get('AZURE_CLI_TEST_MODULES', None):
            display('Test modules list is parsed from environment variable AZURE_CLI_TEST_MODULES.')
            modules = [m.strip() for m in os.environ.get('AZURE_CLI_TEST_MODULES').split(',')]

        selected_modules = filter_user_selected_modules_with_tests(modules, args.profile)
        if not selected_modules:
            display('\nNo tests selected.')
            sys.exit(1)
    else:
        # Otherwise run specific tests
        args.tests = args.tests or []
        # Add any tests from file
        if args.src_file:
            with open(args.src_file, 'r') as f:
                for line in f.readlines():
                    line = line.strip('\r\n')
                    line = line.strip('\n')
                    if line not in args.tests:
                        args.tests.append(line)
        test_paths = []
        selected_modules = []
        for t in args.tests:
            try:
                test_path = os.path.normpath(test_index[t])
                mod_name = extract_module_name(test_path)
                test_paths.append(test_path)
                if mod_name not in selected_modules:
                    selected_modules.append(mod_name)
            except KeyError:
                display("Test '{}' not found.".format(t))
                continue
        selected_modules = filter_user_selected_modules_with_tests(selected_modules, args.profile)
        args.tests = test_paths

    success, failed_tests = run_tests(selected_modules, parallel=args.parallel, run_live=args.live, tests=args.tests)
    # if args.dest_file:
    #     with open(args.dest_file, 'w') as f:
    #         for failed_test in failed_tests:
    #             f.write(failed_test + '\n')
    sys.exit(0 if success else 1)


def validate_usage(args):
    """ Ensure conflicting options aren't specified. """
    test_usage = '[--test TESTS [TESTS ...]] [--src-file FILENAME]'
    ci_usage = '--ci'

    usages = []
    if args.tests or args.src_file:
        usages.append(test_usage)
    if args.ci:
        usages.append(ci_usage)

    if len(usages) > 1:
        display('usage error: ' + ' | '.join(usages))
        sys.exit(1)


def get_current_profile(args):
    import colorama

    colorama.init(autoreset=True)
    try:
        fore_red = colorama.Fore.RED if not IS_WINDOWS else ''
        fore_reset = colorama.Fore.RESET if not IS_WINDOWS else ''
        current_profile = check_output(shlex.split('az cloud show --query profile -otsv'),
                                       shell=IS_WINDOWS).decode('utf-8').strip()
        if not args.profile or current_profile == args.profile:
            args.profile = current_profile
            display('The tests are set to run against current profile {}.'
                    .format(fore_red + current_profile + fore_reset))
        elif current_profile != args.profile:
            display('The tests are set to run against profile {} but the current az cloud profile is {}.'
                    .format(fore_red + args.profile + fore_reset, fore_red + current_profile + fore_reset))
            display('SWITCHING TO PROFILE {}.'.format(fore_red + args.profile + fore_reset))
            display('az cloud update --profile {}'.format(args.profile))
            check_output(shlex.split('az cloud update --profile {}'.format(args.profile)), shell=IS_WINDOWS)
        return current_profile
    except CalledProcessError:
        display('Failed to retrieve current az profile')
        sys.exit(2)


def get_test_index(args):
    test_index_path = os.path.join(get_config_dir(), TEST_INDEX_FORMAT.format(args.profile))
    test_index = {}
    if args.discover:
        test_index = discover_tests(args)
        with open(test_index_path, 'w') as f:
            f.write(json.dumps(test_index))
    elif os.path.isfile(test_index_path):
        with open(test_index_path, 'r') as f:
            test_index = json.loads(''.join(f.readlines()))
    else:
        display('No test index found. Building test index.')
        test_index = discover_tests(args)
        with open(test_index_path, 'w') as f:
            f.write(json.dumps(test_index))
    return test_index


def get_extension_modules():
    from importlib import import_module
    import pkgutil
    from azure.cli.core.extension import get_extensions, get_extension_path, get_extension_modname
    extension_whls = get_extensions()
    ext_modules = []
    if extension_whls:
        for ext_name in [e.name for e in extension_whls]:
            ext_dir = get_extension_path(ext_name)
            sys.path.append(ext_dir)
            try:
                ext_mod = get_extension_modname(ext_name, ext_dir=ext_dir)
                module = import_module(ext_mod)
                setattr(module, 'path', module.__path__[0])
                ext_modules.append((module, ext_mod))
            except Exception as ex:
                display("Error importing '{}' extension: {}".format(ext_mod, ex))
    return ext_modules


def discover_tests(args):
    """ Builds an index of tests so that the user can simply supply the name they wish to test instead of the
        full path. 
    """
    from importlib import import_module
    import pkgutil

    CORE_EXCLUSIONS = ['command_modules', '__main__', 'testsdk']
    profile_split = args.profile.split('-')
    profile_namespace = '_'.join([profile_split[-1]] + profile_split[:-1])

    mods_ns_pkg = import_module('azure.cli.command_modules')
    core_ns_pkg = import_module('azure.cli')
    command_modules = list(pkgutil.iter_modules(mods_ns_pkg.__path__))
    core_modules = list(pkgutil.iter_modules(core_ns_pkg.__path__))
    extensions = get_extension_modules()

    all_modules = command_modules + [x for x in core_modules if x[1] not in CORE_EXCLUSIONS] + extensions

    display("""
==================
  Discover Tests
==================
""")

    module_data = {}
    for mod in all_modules:
        mod_name = mod[1]
        if mod_name == 'core' or mod_name == 'telemetry':
            mod_data = {
                'filepath': os.path.join(mod[0].path, mod_name, 'tests'),
                'base_path': 'azure.cli.{}.tests'.format(mod_name),
                'files': {}
            }
        elif mod_name.startswith('azext_'):
            mod_data = {
                'filepath': os.path.join(mod[0].path, 'tests', profile_namespace),
                'base_path': '{}.tests.{}'.format(mod_name, profile_namespace),
                'files': {}
            }
        else:
            mod_data = {
                'filepath': os.path.join(mod[0].path, mod_name, 'tests', profile_namespace),
                'base_path': 'azure.cli.command_modules.{}.tests.{}'.format(mod_name, profile_namespace),
                'files': {}
            }
        # get the list of test files in each module
        try:
            contents = os.listdir(mod_data['filepath'])
            test_files = {x[:-len('.py')]: {} for x in contents if x.startswith('test_') and x.endswith('.py')}
        except Exception:
            # skip modules that don't have tests
            display("Module '{}' has no tests.".format(mod_name))
            continue

        for file_name in test_files:
            mod_data['files'][file_name] = {}
            test_file_path = mod_data['base_path'] + '.' + file_name
            try:
                module = import_module(test_file_path)
            except ImportError as ex:
                display('Unable to import {}. Reason: {}'.format(test_file_path, ex))
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

        module_data[mod_name] = mod_data

    test_index = {}
    conflicted_keys = []
    def add_to_index(key, path):

        key = key or mod_name
        if key in test_index:
            if key not in conflicted_keys:
                conflicted_keys.append(key)
            mod1 = extract_module_name(path)
            mod2 = extract_module_name(test_index[key])
            if mod1 != mod2:
                # resolve conflicted keys by prefixing with the module name and a dot (.)
                display("\nCOLLISION: Test '{}' exists in both '{}' and '{}'. Resolve using <MOD_NAME>.<NAME>".format(key, mod1, mod2))
                test_index['{}.{}'.format(mod1, key)] = path
                test_index['{}.{}'.format(mod2, key)] = test_index[key]
            else:
                display("\nERROR: Test '{}' exists twice in the '{}' module. Please rename one or both and re-run --discover.".format(key, mod1))
        else:
            test_index[key] = path

    # build the index
    for mod_name, mod_data in module_data.items():
        mod_path = mod_data['filepath']
        for file_name, file_data in mod_data['files'].items():
            file_path = os.path.join(mod_path, file_name) + '.py'
            for class_name, test_list in file_data.items():
                for test_name in test_list:
                    test_path = '{}:{}.{}'.format(file_path, class_name, test_name)
                    add_to_index(test_name, test_path)
                class_path = '{}:{}'.format(file_path, class_name)
                add_to_index(class_name, class_path)
            add_to_index(file_name, file_path)
        add_to_index(mod_name, mod_path)

    # remove the conflicted keys since they would arbitrarily point to a random implementation
    for key in conflicted_keys:
        del test_index[key]

    return test_index


def setup_arguments(parser):
    parser.add_argument('--series', dest='parallel', action='store_false', default=True, help='Disable test parallelization.')
    parser.add_argument('--live', action='store_true', help='Run all the tests live.')
    parser.add_argument(dest='tests', nargs='*',
                        help='Space separated list of tests to run. Can specify test filenames, class name or individual method names.')
    parser.add_argument('--src-file', dest='src_file', help='Text file of test names to include in the the test run.')
    parser.add_argument('--dest-file', dest='dest_file', help='File in which to save the names of any test failures.', default='test_failures.txt')
    parser.add_argument('--ci', dest='ci', action='store_true', help='Run the tests in CI mode.')
    parser.add_argument('--discover', dest='discover', action='store_true', help='Build an index of test names so that you don\'t need to specify '
                                                                                 'fully qualified paths when using --tests.')
    parser.add_argument('--profile', dest='profile', help='Run automation against a specific profile. If omit, the '
                                                          'tests will run against current profile.')
    parser.set_defaults(func=execute)

    return parser


def init_args(root):
    setup_arguments(root.add_parser('test', help='Run test automation'))


def legacy_entry_point():
    sys.stderr.write("The run_tests command is going to be replaced by 'azdev test' command.\n\n")
    args = setup_arguments(argparse.ArgumentParser('Test tools')).parse_args()
    args.func(args)
