# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import sys
import argparse
import shlex
from subprocess import check_output, CalledProcessError

from colorama import Fore

from ..utilities.path import filter_user_selected_modules_with_tests


def execute(args):
    from .main import run_tests, collect_test
    try:
        use_shell = sys.platform.lower() in ['windows', 'win32']
        current_profile = check_output(shlex.split('az cloud show --query profile -otsv'),
                                       shell=use_shell).decode('utf-8').strip()
        if not args.profile:
            args.profile = current_profile
            print('The tests are set to run against current profile {}.'
                  .format(Fore.RED + current_profile + Fore.RESET))
        elif current_profile != args.profile:
            print('The tests are set to run against profile {} but the current az cloud profile is {}.'
                  .format(Fore.RED + args.profile + Fore.RESET, Fore.RED + current_profile + Fore.RESET))
            print('Please use "az cloud set" command to change the current profile.')
            sys.exit(1)
    except CalledProcessError:
        print('Failed to retrieve current az profile')
        sys.exit(2)

    if args.ci:
        selected_modules = [('CI mode', 'azure.cli', 'azure.cli')]
    else:
        if not args.modules and os.environ.get('AZURE_CLI_TEST_MODULES', None):
            print('Test modules list is parsed from environment variable AZURE_CLI_TEST_MODULES.')
            args.modules = [m.strip() for m in os.environ.get('AZURE_CLI_TEST_MODULES').split(',')]

        selected_modules = filter_user_selected_modules_with_tests(args.modules, args.profile)
        if not selected_modules:
            print('No module is selected.')
            sys.exit(1)

    success = run_tests(selected_modules, parallel=args.parallel, run_live=args.live, tests=args.tests)

    sys.exit(0 if success else 1)


def setup_arguments(parser):
    parser.add_argument('--module', dest='modules', nargs='+',
                        help='The modules of which the test to be run. Accept short names, except azure-cli, '
                             'azure-cli-core and azure-cli-nspkg. The modules list can also be set through environment '
                             'variable AZURE_CLI_TEST_MODULES. The value should be a string of space separated module '
                             'names. The environment variable will be overwritten by command line parameters.')
    parser.add_argument('--parallel', action='store_true',
                        help='Run the tests in parallel. This will affect the test output file.')
    parser.add_argument('--live', action='store_true', help='Run all the tests live.')
    parser.add_argument('--test', dest='tests', action='append',
                        help='The specific test to run in the given module. The string can represent a test class or a '
                             'test class and a test method name. Multiple tests can be given, but they should all '
                             'belong to one command modules.')
    parser.add_argument('--ci', dest='ci', action='store_true', help='Run the tests in CI mode.')
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
