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
                                           LargeResponseBodyProcessor, LargeResponseBodyReplacer, RequestUrlNormalizer,
                                           live_only, DeploymentNameReplacer, patch_time_sleep_api, create_random_name)

from azure_devtools.scenario_tests.const import MOCKED_SUBSCRIPTION_ID, ENV_SKIP_ASSERT

from .patches import (patch_load_cached_subscriptions, patch_main_exception_handler,
                      patch_retrieve_token_for_user, patch_long_run_operation_delay,
                      patch_progress_controller)
from .exceptions import CliExecutionError
from .utilities import find_recording_dir

logger = logging.getLogger('azure.cli.testsdk')


class ScenarioTest(ReplayableTest):
    def __init__(self, method_name, config_file=None, recording_name=None,
                 recording_processors=None, replay_processors=None, recording_patches=None, replay_patches=None):
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
                RequestUrlNormalizer(),
                self.name_replacer,
            ],
            replay_processors=replay_processors or [
                LargeResponseBodyReplacer(),
                DeploymentNameReplacer(),
                RequestUrlNormalizer(),
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
            recording_dir=find_recording_dir(inspect.getfile(self.__class__)),
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

    def get_subscription_id(self):
        if self.in_recording or self.is_live:
            subscription_id = self.cmd('account list --query "[?isDefault].id" -o tsv').output.strip()
        else:
            subscription_id = MOCKED_SUBSCRIPTION_ID
        return subscription_id


@live_only()
class LiveScenarioTest(IntegrationTestBase):
    @classmethod
    def cmd(cls, command, checks=None, expect_failure=False):
        return execute(command, expect_failure=expect_failure).assert_with_checks(checks)


class ExecutionResult(object):
    def __init__(self, command, expect_failure=False, in_process=True):
        self.output = ''
        self.applog = ''

        if in_process:
            self._in_process_execute(command, expect_failure=expect_failure)
        else:
            self._out_of_process_execute(command)

        if expect_failure and self.exit_code == 0:
            logger.error('Command "%s" => %d. (It did not fail as expected) Output: %s. %s', command,
                         self.exit_code, self.output, ('Logging ' + self.applog) if self.applog else '')
            raise AssertionError('The command did not fail as it was expected.')
        elif not expect_failure and self.exit_code != 0:
            logger.error('Command "%s" => %d. Output: %s. %s', command, self.exit_code, self.output,
                         ('Logging ' + self.applog) if self.applog else '')
            raise AssertionError('The command failed. Exit code: {}'.format(self.exit_code))

        logger.info('Command "%s" => %d. Output: %s. %s', command, self.exit_code, self.output,
                    ('Logging ' + self.applog) if self.applog else '')

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

    def _in_process_execute(self, command, expect_failure=False):
        from azure.cli.main import main as cli_main
        from six import StringIO
        from vcr.errors import CannotOverwriteExistingCassetteException

        if command.startswith('az '):
            command = command[3:]

        stdout_buf = StringIO()
        logging_buf = StringIO()
        try:
            # issue: stderr cannot be redirect in this form, as a result some failure information
            # is lost when command fails.
            self.exit_code = cli_main(shlex.split(command), output=stdout_buf, logging_stream=logging_buf) or 0
            self.output = stdout_buf.getvalue()
            self.applog = logging_buf.getvalue()

        except CannotOverwriteExistingCassetteException as ex:
            raise AssertionError(ex)
        except CliExecutionError as ex:
            if expect_failure:
                self.exit_code = 1
                self.output = stdout_buf.getvalue()
                self.applog = logging_buf.getvalue()
            elif ex.exception:
                raise ex.exception
            else:
                raise ex
        except Exception as ex:  # pylint: disable=broad-except
            self.exit_code = 1
            self.output = stdout_buf.getvalue()
            self.process_error = ex
        finally:
            stdout_buf.close()
            logging_buf.close()

    def _out_of_process_execute(self, command):
        try:
            self.output = subprocess.check_output(shlex.split(command)).decode('utf-8')
            self.exit_code = 0
        except subprocess.CalledProcessError as error:
            self.exit_code, self.output = error.returncode, error.output.decode('utf-8')
            self.process_error = error


execute = ExecutionResult
