# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import subprocess
import json
import shlex
import logging
import inspect

from azure_devtools.scenario_tests import (IntegrationTestBase, ReplayableTest, SubscriptionRecordingProcessor,
                                           OAuthRequestResponsesFilter, GeneralNameReplacer, LargeRequestBodyProcessor,
                                           LargeResponseBodyProcessor, LargeResponseBodyReplacer, live_only,
                                           DeploymentNameReplacer, patch_time_sleep_api, create_random_name)

from azure_devtools.scenario_tests.const import MOCKED_SUBSCRIPTION_ID, ENV_SKIP_ASSERT

from .patches import (patch_load_cached_subscriptions, patch_main_exception_handler,
                      patch_retrieve_token_for_user, patch_long_run_operation_delay,
                      patch_progress_controller)
from .exceptions import CliExecutionError
from .utilities import find_recording_dir

logger = logging.getLogger('azure.cli.testsdk')


class ScenarioTest(ReplayableTest):
    def __init__(self, method_name, config_file=None,
                 recording_dir=None, recording_name=None,
                 recording_processors=None, replay_processors=None,
                 recording_patches=None, replay_patches=None):
        self.name_replacer = GeneralNameReplacer()
        super(ScenarioTest, self).__init__(
            method_name,
            config_file=config_file,
            recording_processors=recording_processors or [
                SubscriptionRecordingProcessor(MOCKED_SUBSCRIPTION_ID),
                OAuthRequestResponsesFilter(),
                LargeRequestBodyProcessor(),
                LargeResponseBodyProcessor(),
                DeploymentNameReplacer(),
                self.name_replacer,
            ],
            replay_processors=replay_processors or [
                LargeResponseBodyReplacer(),
                DeploymentNameReplacer(),
            ],
            recording_patches=recording_patches or [patch_main_exception_handler],
            replay_patches=replay_patches or [
                patch_main_exception_handler,
                patch_time_sleep_api,
                patch_long_run_operation_delay,
                patch_load_cached_subscriptions,
                patch_retrieve_token_for_user,
                patch_progress_controller,
            ],
            recording_dir=recording_dir or find_recording_dir(inspect.getfile(self.__class__)),
            recording_name=recording_name
        )

    def create_random_name(self, prefix, length):
        self.test_resources_count += 1
        moniker = '{}{:06}'.format(prefix, self.test_resources_count)

        if self.in_recording:
            name = create_random_name(prefix, length)
            self.name_replacer.register_name_pair(name, moniker)
            return name

        return moniker

    @classmethod
    def cmd(cls, command, checks=None, expect_failure=False):
        return execute(command, expect_failure=expect_failure).assert_with_checks(checks)


@live_only()
class LiveScenarioTest(IntegrationTestBase):
    @classmethod
    def cmd(cls, command, checks=None, expect_failure=False):
        return execute(command, expect_failure=expect_failure).assert_with_checks(checks)


class ExecutionResult(object):  # pylint: disable=too-few-public-methods
    def __init__(self, command, expect_failure=False, in_process=True):
        if in_process:
            self._in_process_execute(command)
        else:
            self._out_of_process_execute(command)

        if expect_failure and self.exit_code == 0:
            logger.error('Command "%s" => %d. (It did not fail as expected) Output: %s', command,
                         self.exit_code, self.output)
            raise AssertionError('The command did not fail as it was expected.')
        elif not expect_failure and self.exit_code != 0:
            logger.error('Command "%s" => %d. Output: %s', command, self.exit_code, self.output)
            raise AssertionError('The command failed. Exit code: {}'.format(self.exit_code))

        logger.info('Command "%s" => %d. Output: %s', command, self.exit_code, self.output)

        self.json_value = None
        self.skip_assert = os.environ.get(ENV_SKIP_ASSERT, None) == 'True'

    def assert_with_checks(self, *args):
        checks = []
        for each in args:
            if isinstance(each, list):
                checks.extend(each)
            elif callable(each):
                checks.append(each)

        if not self.skip_assert:
            for c in checks:
                c(self)

        return self

    def get_output_in_json(self):
        if not self.json_value:
            self.json_value = json.loads(self.output)

        if self.json_value is None:
            raise AssertionError('The command output cannot be parsed in json.')

        return self.json_value

    def _in_process_execute(self, command):
        from azure.cli.main import main as cli_main
        from six import StringIO
        from vcr.errors import CannotOverwriteExistingCassetteException

        if command.startswith('az '):
            command = command[3:]

        output_buffer = StringIO()
        try:
            # issue: stderr cannot be redirect in this form, as a result some failure information
            # is lost when command fails.
            self.exit_code = cli_main(shlex.split(command), file=output_buffer) or 0
            self.output = output_buffer.getvalue()
        except CannotOverwriteExistingCassetteException as ex:
            raise AssertionError(ex)
        except CliExecutionError as ex:
            if ex.exception:
                raise ex.exception
            else:
                raise ex
        except Exception as ex:  # pylint: disable=broad-except
            self.exit_code = 1
            self.output = output_buffer.getvalue()
            self.process_error = ex
        finally:
            output_buffer.close()

    def _out_of_process_execute(self, command):
        try:
            self.output = subprocess.check_output(shlex.split(command)).decode('utf-8')
            self.exit_code = 0
        except subprocess.CalledProcessError as error:
            self.exit_code, self.output = error.returncode, error.output.decode('utf-8')
            self.process_error = error


execute = ExecutionResult
