from __future__ import print_function

import json
import os
import traceback

from six import StringIO

from azure.cli.main import main as cli
from azure.cli.parser import IncorrectUsageError

class CommandTestScript(object):

    def __init__(self):
        self._display = StringIO()
        self._raw = StringIO()
        self.display_result = ''
        self.raw_result = ''
        self.auto = True
        self.fail = False

    def set_up(self):
        pass

    def run_test(self):
        try:
            self.set_up()
            self.test_body()
        except Exception: #pylint: disable=broad-except
            traceback.print_exc(file=self._display)
            self.fail = True
        finally:
            self.tear_down()
            self._tear_down()

    def test_body(self):
        raise NotImplementedError()

    def tear_down(self):
        pass

    def _tear_down(self):
        self.display_result = self._display.getvalue()
        self.raw_result = self._raw.getvalue()
        self._display.close()
        self._raw.close()

    def rec(self, command):
        ''' Run a command and save the output as part of the expected results. This will also
        save the output to a display file so you can see the command, followed by its output
        in order to determine if the output is acceptable. Invoking this command in a script
        turns off the flag that signals the test is fully automatic. '''
        self.auto = False
        output = StringIO()
        cli(command.split(), file=output)
        result = output.getvalue().strip()
        self._display.write('\n\n== {} ==\n\n{}'.format(command, result))
        self._raw.write(result)
        output.close()
        return result

    def run(self, command): #pylint: disable=no-self-use
        ''' Run a command without recording the output as part of expected results. Useful if you
        need to run a command for branching logic or just to reset back to a known condition. '''
        output = StringIO()
        cli(command.split(), file=output)
        result = output.getvalue().strip()
        output.close()
        return result

    def test(self, command, checks):
        ''' Runs a command with the json output format and validates the input against the provided
        checks. Multiple JSON properties can be submitted as a dictionary and are treated as an AND
        condition. '''
        def _check_json(source, checks):
            for check in checks.keys():
                if isinstance(checks[check], dict) and check in source:
                    _check_json(source[check], checks[check])
                else:
                    assert source[check] == checks[check]

        output = StringIO()
        command += ' -o json'
        cli(command.split(), file=output)
        result = output.getvalue().strip()
        self._raw.write(result)
        if isinstance(checks, bool):
            result_val = str(result).lower().replace('"', '')
            bool_val = result_val in ('yes', 'true', 't', '1')
            try:
                assert bool_val == checks
            except AssertionError as ex:
                print('COMMAND FAILED: {}'.format(command))
                print("EXPECTED: {} ACTUAL: {} RESULT: {}".format(checks, result_val, bool_val))
                raise ex
        elif isinstance(checks, dict):
            json_val = json.loads(result)
            _check_json(json_val, checks)
        elif checks is None:
            assert result is None or result == ''
        else:
            raise IncorrectUsageError('test only accepts a dictionary of json properties or ' + \
                                      'a boolean value.')
    def set_env(self, key, val): #pylint: disable=no-self-use
        os.environ[key] = val

    def pop_env(self, key): #pylint: disable=no-self-use
        return os.environ.pop(key, None)

    def print_(self, string):
        ''' Write free text to the display output only. This text will not be included in the
        raw saved output and using this command does not flag a test as requiring manual
        verification. '''
        self._display.write('\n{}'.format(string))
