from __future__ import print_function

import json
import os
import traceback
import collections
import jmespath
from six import StringIO

from azure.cli.main import main as cli
from azure.cli.parser import IncorrectUsageError
from azure.cli._util import CLIError

TRACK_COMMANDS = os.environ.get('AZURE_CLI_TEST_TRACK_COMMANDS')
COMMAND_COVERAGE_FILENAME = 'command_coverage.txt'

class JMESPathComparatorAssertionError(AssertionError):

    def __init__(self, comparator, actual_result, json_data):
        message = "Actual value '{}' != Expected value '{}'. ".format(
            actual_result,
            comparator.expected_result)
        message += "Query '{}' used on json data '{}'".format(comparator.query, json_data)
        super(JMESPathComparatorAssertionError, self).__init__(message)

class JMESPathComparator(object): #pylint: disable=too-few-public-methods

    def __init__(self, query, expected_result):
        self.query = query
        self.expected_result = expected_result

    def compare(self, json_data):
        json_val = json.loads(json_data)
        actual_result = jmespath.search(
            self.query,
            json_val,
            jmespath.Options(collections.OrderedDict))
        if not actual_result == self.expected_result:
            raise JMESPathComparatorAssertionError(self, actual_result, json_data)

def _check_json(source, checks):

    def _check_json_child(item, checks):
        for check in checks.keys():
            if isinstance(checks[check], dict) and check in item:
                return _check_json_child(item[check], checks[check])
            else:
                return item[check] == checks[check]

    if not isinstance(source, list):
        source = [source]
    passed = False
    for item in source:
        passed = _check_json_child(item, checks)
        if passed:
            break
    return passed

class CommandTestScript(object): #pylint: disable=too-many-instance-attributes

    def __init__(self, set_up, test_body, tear_down):
        self._display = StringIO()
        self._raw = StringIO()
        self.display_result = ''
        self.debug = False
        self.raw_result = ''
        self.auto = True
        self.fail = False
        self.set_up = set_up
        if hasattr(test_body, '__call__'):
            self.test_body = test_body
        else:
            raise TypeError('test_body must be callable')
        self.tear_down = tear_down
        self.track_commands = False

    def run_test(self):
        try:
            if hasattr(self.set_up, '__call__'):
                self.set_up()
            # only track commands for the test body
            self.track_commands = TRACK_COMMANDS
            self.test_body()
            self.track_commands = False
        except Exception: #pylint: disable=broad-except
            traceback.print_exc(file=self._display)
            self.fail = True
        finally:
            if hasattr(self.tear_down, '__call__'):
                self.tear_down()
            self.display_result = self._display.getvalue()
            self.raw_result = self._raw.getvalue()
            self._display.close()
            self._raw.close()

    def _track_executed_commands(self, command):
        if not self.track_commands:
            return
        filename = COMMAND_COVERAGE_FILENAME
        with open(filename, 'a+') as f:
            f.write(' '.join(command))
            f.write('\n')

    def rec(self, command):
        ''' Run a command and save the output as part of the expected results. This will also
        save the output to a display file so you can see the command, followed by its output
        in order to determine if the output is acceptable. Invoking this command in a script
        turns off the flag that signals the test is fully automatic. '''
        if self.debug:
            print('RECORDING: {}'.format(command))
        self.auto = False
        output = StringIO()
        command_list = command if isinstance(command, list) else command.split()
        cli(command_list, file=output)
        self._track_executed_commands(command_list)
        result = output.getvalue().strip()
        self._display.write('\n\n== {} ==\n\n{}'.format(command, result))
        self._raw.write(result)
        output.close()
        return result

    def run(self, command): #pylint: disable=no-self-use
        ''' Run a command without recording the output as part of expected results. Useful if you
        need to run a command for branching logic or just to reset back to a known condition. '''
        if self.debug:
            print('RUNNING: {}'.format(command))
        output = StringIO()
        command_list = command if isinstance(command, list) else command.split()
        cli(command_list, file=output)
        self._track_executed_commands(command_list)
        result = output.getvalue().strip()
        output.close()
        if isinstance(command, str) and '-o json' in command:
            result = json.loads(result)
        elif isinstance(command, list) and set(command).issuperset(set(['-o', 'json'])):
            result = json.loads(result)
        return result

    def test(self, command, checks):
        ''' Runs a command with the json output format and validates the input against the provided
        checks. Multiple JSON properties can be submitted as a dictionary and are treated as an AND
        condition. '''
        if self.debug:
            print('TESTING: {}'.format(command))
        output = StringIO()
        command_list = command if isinstance(command, list) else command.split()
        command_list += ['-o', 'json']
        cli(command_list, file=output)
        self._track_executed_commands(command_list)
        result = output.getvalue().strip()
        self._raw.write(result)
        try:
            if isinstance(checks, list) and all(
                    isinstance(comparator, JMESPathComparator) for comparator in checks):
                for comparator in checks:
                    comparator.compare(result)
            elif isinstance(checks, JMESPathComparator):
                checks.compare(result)
            elif isinstance(checks, bool):
                result_val = str(result).lower().replace('"', '')
                result = result_val in ('yes', 'true', 't', '1')
                assert result == checks
            elif isinstance(checks, str):
                assert result.replace('"', '') == checks
            elif isinstance(checks, dict):
                json_val = json.loads(result)
                assert _check_json(json_val, checks)
            elif checks is None:
                assert result is None or result == ''
            else:
                raise IncorrectUsageError('unsupported type \'{}\' in test'.format(type(checks)))
        except AssertionError:
            raise CLIError('COMMAND {} FAILED. Result: {} Checks: {}'.format(
                command, result, checks))
    def set_env(self, key, val): #pylint: disable=no-self-use
        os.environ[key] = val

    def pop_env(self, key): #pylint: disable=no-self-use
        return os.environ.pop(key, None)

    def display(self, string):
        ''' Write free text to the display output only. This text will not be included in the
        raw saved output and using this command does not flag a test as requiring manual
        verification. '''
        self._display.write('\n{}'.format(string))
