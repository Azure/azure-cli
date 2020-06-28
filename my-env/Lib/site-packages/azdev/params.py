# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

# pylint: disable=line-too-long
import argparse

from knack.arguments import ArgumentsContext, CLIArgumentType

from azdev.completer import get_test_completion
from azdev.operations.linter import linter_severity_choices


class Flag(object):
    """ Place holder to be used for optionals that take 0 or more arguments """


# pylint: disable=too-many-statements
def load_arguments(self, _):

    modules_type = CLIArgumentType(nargs='*',
                                   help="Space-separated list of modules or extensions (dev mode) to check. "
                                        "Use 'CLI' to check built-in modules or 'EXT' to check extensions. "
                                        "Omit to check all. ")

    with ArgumentsContext(self, '') as c:
        c.argument('private', action='store_true', help='Target the private repo.')
        c.argument('yes', options_list=['--yes', '-y'], action='store_true', help='Answer "yes" to all prompts.')
        c.argument('use_ext_index', action='store_true', help='Run command on extensions registered in the azure-cli-extensions index.json.')
        c.argument('git_source', options_list='--src', arg_group='Git', help='Name of the Git source branch to check (i.e. master or upstream/master).')
        c.argument('git_target', options_list='--tgt', arg_group='Git', help='Name of the Git target branch to check (i.e. dev or upstream/dev)')
        c.argument('git_repo', options_list='--repo', arg_group='Git', help='Path to the Git repo to check.')

    with ArgumentsContext(self, 'setup') as c:
        c.argument('cli_path', options_list=['--cli', '-c'], nargs='?', const=Flag, help="Path to an existing Azure CLI repo. Omit value to search for the repo or use special value 'EDGE' to install the latest developer edge build.")
        c.argument('ext_repo_path', options_list=['--repo', '-r'], nargs='+', help='Space-separated list of paths to existing Azure CLI extensions repos.')
        c.argument('ext', options_list=['--ext', '-e'], nargs='+', help="Space-separated list of extensions to install initially. Use '*' to install all extensions.")
        c.argument('deps', options_list=['--deps-from', '-d'], choices=['requirements.txt', 'setup.py'], default='requirements.txt', help="Choose the file to resolve dependencies.")

    with ArgumentsContext(self, 'test') as c:
        c.argument('discover', options_list='--discover', action='store_true', help='Build an index of test names so that you don\'t need to specify fully qualified test paths.')
        c.argument('xml_path', options_list='--xml-path', help='Path and filename at which to store the results in XML format. If omitted, the file will be saved as `test_results.xml` in your `.azdev` directory.')
        c.argument('in_series', options_list='--series', action='store_true', help='Disable test parallelization.')
        c.argument('run_live', options_list='--live', action='store_true', help='Run all tests live.')

        c.positional('tests', nargs='*',
                     help="Space-separated list of tests to run. Can specify module or extension names, test filenames, class name or individual method names. "
                          "Omit to check all or use 'CLI' or 'EXT' to check only CLI modules or extensions respectively.",
                     completer=get_test_completion)
        c.argument('profile', options_list='--profile', help='Run automation against a specific profile. If omit, the tests will run against current profile.')
        c.argument('pytest_args', nargs=argparse.REMAINDER, options_list=['--pytest-args', '-a'], help='Denotes the remaining args will be passed to pytest.')
        c.argument('last_failed', options_list='--lf', action='store_true', help='Re-run the last tests that failed.')
        c.argument('no_exit_first', options_list='--no-exitfirst', action='store_true', help='Do not exit on first error or failed test')

        # CI parameters
        c.argument('cli_ci',
                   action='store_true',
                   arg_group='Continuous Integration',
                   help='Apply incremental test strategy to Azure CLI on Azure DevOps')

    with ArgumentsContext(self, 'coverage') as c:
        c.argument('prefix', type=str, help='Filter analysis by command prefix.')
        c.argument('report', action='store_true', help='Display results as a report.')
        c.argument('untested_params', nargs='+', help='Space-separated list of param dest values to search for (OR logic)')

    with ArgumentsContext(self, 'style') as c:
        c.positional('modules', modules_type)
        c.argument('pylint', action='store_true', help='Run pylint.')
        c.argument('pep8', action='store_true', help='Run flake8 to check PEP8.')

    with ArgumentsContext(self, 'cli check-versions') as c:
        c.argument('update', action='store_true', help='If provided, the command will update the versions in azure-cli\'s setup.py file.')
        c.argument('pin', action='store_true', help='If provided and used with --update, will pin the module versions in azure-cli\'s setup.py file.')

    with ArgumentsContext(self, 'cli update-setup') as c:
        c.argument('pin', action='store_true', help='Pin the module versions in azure-cli\'s setup.py file.')

    # region linter
    with ArgumentsContext(self, 'linter') as c:
        c.positional('modules', modules_type)
        c.argument('rules', options_list=['--rules', '-r'], nargs='+', help='Space-separated list of rules to run. Omit to run all rules.')
        c.argument('rule_types', options_list=['--rule-types', '-t'], nargs='+', choices=['params', 'commands', 'command_groups', 'help_entries'], help='Space-separated list of rule types to run. Omit to run all.')
        c.argument('ci_exclusions', action='store_true', help='Force application of CI exclusions list when run locally.')
        c.argument('include_whl_extensions',
                   action='store_true',
                   help="Allow running linter on extensions installed by `az extension add`.")
        c.argument('save_global_exclusion',
                   action='store_true',
                   options_list=['--save', '-s'],
                   help="Allow saving global exclusion. It would take effect when modules is CLI or EXT.",
                   deprecate_info=c.deprecate(hide=True))
        c.argument('min_severity', choices=linter_severity_choices(),
                   help='The minimum severity level to run the linter on. '
                        'For example, specifying "medium" runs linter rules that have "high" or "medium" severity. '
                        'However, specifying "low" runs the linter on every rule, regardless of severity. '
                        'Defaults to "high".')
    # endregion

    with ArgumentsContext(self, 'perf') as c:
        c.argument('runs', type=int, help='Number of runs to average performance over.')

    with ArgumentsContext(self, 'extension') as c:
        c.argument('dist_dir', help='Name of a directory in which to save the resulting WHL files.')

    with ArgumentsContext(self, 'extension publish') as c:
        c.argument('update_index', action='store_true', help='Update the index.json file after publishing is complete.')

    with ArgumentsContext(self, 'extension publish') as c:
        c.argument('storage_account', help='Name of the storage account to publish to. Environment variable: AZDEV_DEFAULTS_STORAGE_ACCOUNT.', arg_group='Storage', configured_default='storage_account')
        c.argument('storage_container', help='Name of the storage container to publish to. Environment variable: AZDEV_DEFAULTS_STORAGE_CONTAINER.', arg_group='Storage', configured_default='storage_container')
        c.argument('storage_account_key', help='Key of the storage account to publish to. ', arg_group='Storage',
                   configured_default='storage_account')

    for scope in ['extension add', 'extension remove', 'extension build', 'extension publish']:
        with ArgumentsContext(self, scope) as c:
            c.positional('extensions', metavar='NAME', nargs='+', help='Space-separated list of extension names.')

    for scope in ['extension repo add', 'extension repo remove']:
        with ArgumentsContext(self, scope) as c:
            c.positional('repos', metavar='PATH', nargs='+', help='Space-separated list of paths to Git repositories.')

    with ArgumentsContext(self, 'extension update-index') as c:
        c.positional('extensions', nargs='+', metavar='URL', help='Space-separated list of URLs to extension WHL files.')

    with ArgumentsContext(self, 'cli create') as c:
        c.positional('mod_name', help='Name of the module to create.')

    with ArgumentsContext(self, 'cli create') as c:
        c.ignore('local_sdk')

    with ArgumentsContext(self, 'extension create') as c:
        c.positional('ext_name', help='Name of the extension to create.')

    for scope in ['extension create', 'cli create']:
        with ArgumentsContext(self, scope) as c:
            c.argument('github_alias', help='Github alias for the individual who will be the code owner for this package.')
            c.argument('not_preview', action='store_true', help='Do not create template commands under a "Preview" status.')
            c.argument('required_sdk', help='Name and version of the underlying Azure SDK that is published on PyPI. (ex: azure-mgmt-contoso==0.1.0).', arg_group='SDK')
            c.argument('local_sdk', help='Path to a locally saved SDK. Use if your SDK is not available on PyPI.', arg_group='SDK')
            c.argument('client_name', help='Name of the Python SDK client object (ex: ContosoManagementClient).', arg_group='SDK')
            c.argument('operation_name', help='Name of the principal Python SDK operation class (ex: ContosoOperations).', arg_group='SDK')
            c.argument('sdk_property', help='The name of the Python variable that describes the main object name in the SDK calls (i.e.: account_name)', arg_group='SDK')
            c.argument('repo_name', help='Name of the repo the extension will exist in.')
            c.argument('display_name', arg_group='Help', help='Description to display in help text.')
            c.argument('display_name_plural', arg_group='Help', help='Description to display in help text when plural.')

    with ArgumentsContext(self, 'cli generate-docs') as c:
        c.argument('all_profiles', action='store_true',
                   help="If specified, generate docs for all CLI profiles. NOTE: this command updates the current CLI profile and will attempt to reset it to its original value. "
                        "Please check the CLI's profile after running this command.")

    for scope in ['cli', 'extension']:
        with ArgumentsContext(self, '{} generate-docs'.format(scope)) as c:

            c.argument('output_dir', help='Directory to place the generated docs in. Defaults to a temporary directory. '
                                          'If the base directory does not exist, it will be created')
            c.argument('output_type', choices=['xml', 'html', 'text', 'man', 'latex'], default="xml",
                       help='Output type of the generated docs.')
