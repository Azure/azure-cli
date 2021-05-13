# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import collections
import json
import os
import os.path
import sys

import automation.tests.nose_helper as automation_tests
import automation.utilities.path as automation_path


def init(root):
    command_coverage = root.add_parser('command', help='Examine command and parameter test coverage.')
    command_coverage.add_argument('--prefix', dest='prefix', default='', help='Filter results by string prefix.')
    command_coverage.add_argument('--report', action='store_true', help='Display a report of summary statistics for the run.')
    command_coverage.add_argument('--untested-params', help='Return commands for which any of these parameters (space-separated) are untested.')
    command_coverage.add_argument('--projection', help='Filter output to only return the specific properties (space-separated).')
    command_coverage.set_defaults(func=run_command_coverage)


def _build_coverage_data(executed_commands):
    coverage_data = {}
    for command in executed_commands:
        command_tokens = []
        param_tokens = []
        is_command = True
        for token in command.split():
            if token.startswith('-'):
                param_tokens.append(token)
                is_command = False
            elif is_command:
                command_tokens.append(token)
            else:
                # this would be a value token... meh.
                pass
        command_name = ' '.join(command_tokens)
        if command_name in coverage_data:
            coverage_data[command_name] = list(set(coverage_data[command_name]).union(set(param_tokens)))
        else:
            coverage_data[command_name] = param_tokens
    return coverage_data


def _build_command_report(command_summary):

    report_summary = {}

    for command, data in command_summary.items():

        OVERALL = 'OVERALL'

        command_tokens = command.split(' ')
        first_level = command_tokens[0]
        try:
            second_level = command_tokens[1]
        except IndexError:
            # group top level commands under a "_TOP_" group
            second_level = first_level
            first_level = '_TOP_'

        # determine if command should be reported as a command or subgroup
        try:
            _ = command_tokens[2]
        except IndexError:
            second_level = 'COMMANDS'

        # enter command into report summary
        if first_level not in report_summary:
            report_summary[first_level] = {
                OVERALL: {
                    '_commands_total': 0,
                    '_commands_tested': 0,
                    '_params_total': 0,
                    '_params_tested': 0,
                }
            }

        if second_level not in report_summary[first_level]:
            report_summary[first_level][second_level] = {
                '_commands_total': 0,
                '_commands_tested': 0,
                '_params_total': 0,
                '_params_tested': 0,
            }

        report_summary[first_level][OVERALL]['_commands_total'] += 1
        report_summary[first_level][OVERALL]['_commands_tested'] += 1 if data['tested'] else 0

        report_summary[first_level][second_level]['_commands_total'] += 1
        report_summary[first_level][second_level]['_commands_tested'] += 1 if data['tested'] else 0

        params_tested = len(data['tested_params'])
        # only count param statistics if the command is tested
        params_total = params_tested + len(data['untested_params']) if data['tested'] else 0

        report_summary[first_level][OVERALL]['_params_tested'] += params_tested
        report_summary[first_level][OVERALL]['_params_total'] += params_total

        report_summary[first_level][second_level]['_params_tested'] += params_tested
        report_summary[first_level][second_level]['_params_total'] += params_total

    # calculate summary values and clean up
    for val in report_summary.values():
        for data in val.values():
            command_score = data['_commands_tested'] * 1.0 / data['_commands_total']
            try:
                param_score = data['_params_tested'] * 1.0 / data['_params_total']
            except ZeroDivisionError:
                param_score = 0
            del data['_commands_tested']
            del data['_commands_total']
            del data['_params_tested']
            del data['_params_total']
            data['command_score'] = '{0:.2f}'.format(command_score)
            data['param_score'] = '{0:.2f}'.format(param_score)

    return report_summary


def run_command_coverage(args):

    from azure.cli.core import get_default_cli
    from azure.cli.core.file_util import create_invoker_and_load_cmds_and_args
    from azure.cli.testsdk.base import ENV_COMMAND_COVERAGE, COVERAGE_FILE

    print("""
    *******************************
    * AZURE CLI 2.0 TEST COVERAGE *
    *******************************

    This script is in development. Before using, ensure you have run your tests with the environment variable
    '{}' set to True! This script will not run the tests for you. Commands from test runs are aggregated in the
    '{}' file.


""".format(ENV_COMMAND_COVERAGE, COVERAGE_FILE), file=sys.stderr)

    prefix = args.prefix
    report = args.report
    untested_params = args.untested_params
    projection = args.projection

    executed_commands = []
    with open(COVERAGE_FILE, 'r') as f:
        executed_commands = f.readlines()

    coverage_data = _build_coverage_data(executed_commands)

    cli = get_default_cli()
    create_invoker_and_load_cmds_and_args(cli)
    command_table = cli.invocation.commands_loader.command_table

    def _lookup_dest(opt, command_args):
        for dest, arg in command_args.items():
            if opt in arg.options_list:
                return dest

    all_commands = set(command_table.keys())
    command_summary = {}

    commands_to_check = [x for x in all_commands if x.startswith(prefix)]

    for command in commands_to_check:

        # enter command into command summary
        if command not in command_summary:
            command_summary[command] = {
                'command': command,
                'tested': command in coverage_data,  # if the command is tested
                'live_only': None,  # if the command is tested live only (less ideal)
                'record_only': None,  # if command is tested with @record_only (less ideal)
                'param_score': 0.0,  # num_tested_params / total_params
                'tested_params': [],  # list of tested params
                'untested_params': []  # list of untested params
            }

        covered_params = coverage_data.get(command, [])
        command_arguments = command_table[command].arguments
        parameter_summary = {}
        for key, val in command_arguments.items():
            # ignore generic update args
            if key in ['properties_to_add', 'properties_to_remove', 'properties_to_set']:
                continue
            # ignore suppressed args
            if val.type.settings.get('help', '') == '==SUPPRESS==':
                continue
            parameter_summary[key] = False
        for cp in covered_params:
            dest = _lookup_dest(cp, command_arguments)
            parameter_summary[dest] = True
        for k, v in parameter_summary.items():
            if not v:
                command_summary[command]['untested_params'].append(k)
            else:
                command_summary[command]['tested_params'].append(k)
        total_param_count = len(parameter_summary)
        tested_param_count = total_param_count - len(command_summary[command]['untested_params'])
        command_summary[command]['param_score'] = tested_param_count * 1.0 / total_param_count if \
            total_param_count else 1.0

    # Filter results
    if prefix:
        command_summary = {k: v for k, v in command_summary.items() if k.startswith(prefix)}

    if untested_params:
        command_summary = {k: v for k, v in command_summary.items() if untested_params in v['untested_params']}

    if not report:
        final_values = []
        if projection:
            for entry in command_summary.values():
                final_values.append({k: v for k, v in entry.items() if k in projection})
        if not final_values:
            final_values = list(command_summary.values())
        print(json.dumps(final_values, indent=4, sort_keys=True))
    else:
        report_summary = _build_command_report(command_summary)
        spacing_format = '{0:<20s} {1:<40s} {2:<10s} {3:<10s}'
        print(spacing_format.format('MODULE', 'GROUP', 'COMMAND', 'PARAM'))
        for mod, mod_data in report_summary.items():
            for group, group_data in mod_data.items():
                print(spacing_format.format(
                    mod, group, group_data['command_score'], group_data['param_score']))


if __name__ == '__main__':
    main()
