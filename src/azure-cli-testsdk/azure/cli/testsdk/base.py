# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import json
import shlex
import logging
import inspect
import unittest
import tempfile

from .scenario_tests import (IntegrationTestBase, ReplayableTest, SubscriptionRecordingProcessor,
                             LargeRequestBodyProcessor,
                             LargeResponseBodyProcessor, LargeResponseBodyReplacer, RequestUrlNormalizer,
                             GeneralNameReplacer,
                             live_only, DeploymentNameReplacer, patch_time_sleep_api, create_random_name)

from .scenario_tests.const import MOCKED_SUBSCRIPTION_ID, ENV_SKIP_ASSERT

from .patches import (patch_load_cached_subscriptions, patch_main_exception_handler,
                      patch_retrieve_token_for_user, patch_long_run_operation_delay,
                      patch_progress_controller, patch_get_current_system_username)
from .exceptions import CliExecutionError
from .utilities import (find_recording_dir, StorageAccountKeyReplacer, GraphClientPasswordReplacer,
                        AADAuthRequestFilter)
from .reverse_dependency import get_dummy_cli

logger = logging.getLogger('azure.cli.testsdk')


ENV_COMMAND_COVERAGE = 'AZURE_CLI_TEST_COMMAND_COVERAGE'
COVERAGE_FILE = 'az_command_coverage.txt'


class CheckerMixin(object):

    def _apply_kwargs(self, val):
        try:
            return val.format(**self.kwargs)
        except AttributeError:
            return val
        except KeyError as ex:
            # due to mis-spelled kwarg
            raise KeyError("Key '{}' not found in kwargs. Check spelling and ensure it has been registered."
                           .format(ex.args[0]))

    def check(self, query, expected_results, case_sensitive=True):
        from azure.cli.testsdk.checkers import JMESPathCheck
        query = self._apply_kwargs(query)
        expected_results = self._apply_kwargs(expected_results)
        return JMESPathCheck(query, expected_results, case_sensitive)

    def exists(self, query):
        from azure.cli.testsdk.checkers import JMESPathCheckExists
        query = self._apply_kwargs(query)
        return JMESPathCheckExists(query)

    def not_exists(self, query):
        from azure.cli.testsdk.checkers import JMESPathCheckNotExists
        query = self._apply_kwargs(query)
        return JMESPathCheckNotExists(query)

    def greater_than(self, query, expected_results):
        from azure.cli.testsdk.checkers import JMESPathCheckGreaterThan
        query = self._apply_kwargs(query)
        expected_results = self._apply_kwargs(expected_results)
        return JMESPathCheckGreaterThan(query, expected_results)

    def check_pattern(self, query, expected_results):
        from azure.cli.testsdk.checkers import JMESPathPatternCheck
        query = self._apply_kwargs(query)
        expected_results = self._apply_kwargs(expected_results)
        return JMESPathPatternCheck(query, expected_results)

    def is_empty(self):  # pylint: disable=no-self-use
        from azure.cli.testsdk.checkers import NoneCheck
        return NoneCheck()


class ScenarioTest(ReplayableTest, CheckerMixin, unittest.TestCase):
    def __init__(self, method_name, config_file=None, recording_name=None,
                 recording_processors=None, replay_processors=None, recording_patches=None, replay_patches=None):
        self.cli_ctx = get_dummy_cli()
        self.name_replacer = GeneralNameReplacer()
        self.kwargs = {}
        self.test_guid_count = 0
        self._processors_to_reset = [StorageAccountKeyReplacer(), GraphClientPasswordReplacer()]
        default_recording_processors = [
            SubscriptionRecordingProcessor(MOCKED_SUBSCRIPTION_ID),
            AADAuthRequestFilter(),
            LargeRequestBodyProcessor(),
            LargeResponseBodyProcessor(),
            DeploymentNameReplacer(),
            RequestUrlNormalizer(),
            self.name_replacer
        ] + self._processors_to_reset

        default_replay_processors = [
            LargeResponseBodyReplacer(),
            DeploymentNameReplacer(),
            RequestUrlNormalizer(),
        ]

        default_recording_patches = [patch_main_exception_handler]

        default_replay_patches = [
            patch_main_exception_handler,
            patch_time_sleep_api,
            patch_long_run_operation_delay,
            patch_load_cached_subscriptions,
            patch_retrieve_token_for_user,
            patch_progress_controller,
        ]

        def _merge_lists(base, patches):
            merged = list(base)
            if patches and not isinstance(patches, list):
                patches = [patches]
            if patches:
                merged = list(set(merged).union(set(patches)))
            return merged

        super(ScenarioTest, self).__init__(
            method_name,
            config_file=config_file,
            recording_processors=_merge_lists(default_recording_processors, recording_processors),
            replay_processors=_merge_lists(default_replay_processors, replay_processors),
            recording_patches=_merge_lists(default_recording_patches, recording_patches),
            replay_patches=_merge_lists(default_replay_patches, replay_patches),
            recording_dir=find_recording_dir(inspect.getfile(self.__class__)),
            recording_name=recording_name
        )

    def tearDown(self):
        for processor in self._processors_to_reset:
            processor.reset()
        super(ScenarioTest, self).tearDown()

    def create_random_name(self, prefix, length):
        self.test_resources_count += 1
        moniker = '{}{:06}'.format(prefix, self.test_resources_count)

        if self.in_recording:
            name = create_random_name(prefix, length)
            self.name_replacer.register_name_pair(name, moniker)
            return name

        return moniker

    # Use this helper to make playback work when guids are created and used in request urls, e.g. role assignment or AAD
    # service principals. For usages, in test code, patch the "guid-gen" routine to this one, e.g.
    # with mock.patch('azure.cli.command_modules.role.custom._gen_guid', side_effect=self.create_guid)
    def create_guid(self):
        import uuid
        self.test_guid_count += 1
        moniker = '88888888-0000-0000-0000-00000000' + ("%0.4x" % self.test_guid_count)

        if self.in_recording:
            name = uuid.uuid4()
            self.name_replacer.register_name_pair(str(name), moniker)
            return name

        return uuid.UUID(moniker)

    def cmd(self, command, checks=None, expect_failure=False):
        command = self._apply_kwargs(command)
        return execute(self.cli_ctx, command, expect_failure=expect_failure).assert_with_checks(checks)

    def get_subscription_id(self):
        if self.in_recording or self.is_live:
            subscription_id = self.cmd('account list --query "[?isDefault].id" -o tsv').output.strip()
        else:
            subscription_id = MOCKED_SUBSCRIPTION_ID
        return subscription_id


class LocalContextScenarioTest(ScenarioTest):
    def __init__(self, method_name, config_file=None, recording_name=None, recording_processors=None,
                 replay_processors=None, recording_patches=None, replay_patches=None, working_dir=None):
        super(LocalContextScenarioTest, self).__init__(method_name, config_file, recording_name, recording_processors,
                                                       replay_processors, recording_patches, replay_patches)
        if self.in_recording:
            self.recording_patches.append(patch_get_current_system_username)
        else:
            self.replay_patches.append(patch_get_current_system_username)
        self.original_working_dir = os.getcwd()
        if working_dir:
            self.working_dir = working_dir
        else:
            self.working_dir = tempfile.mkdtemp()

    def setUp(self):
        super(LocalContextScenarioTest, self).setUp()
        self.cli_ctx.local_context.initialize()
        os.chdir(self.working_dir)
        self.cmd('local-context on')

    def tearDown(self):
        super(LocalContextScenarioTest, self).tearDown()
        self.cmd('local-context off')
        self.cmd('local-context delete --all --purge -y')
        os.chdir(self.original_working_dir)
        if os.path.exists(self.working_dir):
            import shutil
            shutil.rmtree(self.working_dir)


@live_only()
class LiveScenarioTest(IntegrationTestBase, CheckerMixin, unittest.TestCase):

    def __init__(self, method_name):
        super(LiveScenarioTest, self).__init__(method_name)
        self.cli_ctx = get_dummy_cli()
        self.kwargs = {}
        self.test_resources_count = 0

    def setUp(self):
        patch_main_exception_handler(self)

    def cmd(self, command, checks=None, expect_failure=False):
        command = self._apply_kwargs(command)
        return execute(self.cli_ctx, command, expect_failure=expect_failure).assert_with_checks(checks)

    def get_subscription_id(self):
        return self.cmd('account list --query "[?isDefault].id" -o tsv').output.strip()


class ExecutionResult(object):
    def __init__(self, cli_ctx, command, expect_failure=False):
        self.output = ''
        self.applog = ''
        self.command_coverage = {}
        cli_ctx.data['_cache'] = None

        if os.environ.get(ENV_COMMAND_COVERAGE, None):
            with open(COVERAGE_FILE, 'a') as coverage_file:
                if command.startswith('az '):
                    command = command[3:]
                coverage_file.write(command + '\n')

        self._in_process_execute(cli_ctx, command, expect_failure=expect_failure)

        log_val = ('Logging ' + self.applog) if self.applog else ''
        if expect_failure and self.exit_code == 0:
            logger.error('Command "%s" => %d. (It did not fail as expected). %s\n', command,
                         self.exit_code, log_val)
            raise AssertionError('The command did not fail as it was expected.')
        if not expect_failure and self.exit_code != 0:
            logger.error('Command "%s" => %d. %s\n', command, self.exit_code, log_val)
            raise AssertionError('The command failed. Exit code: {}'.format(self.exit_code))

        logger.info('Command "%s" => %d. %s\n', command, self.exit_code, log_val)

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

    def _in_process_execute(self, cli_ctx, command, expect_failure=False):
        from io import StringIO
        from vcr.errors import CannotOverwriteExistingCassetteException

        if command.startswith('az '):
            command = command[3:]

        stdout_buf = StringIO()
        logging_buf = StringIO()
        try:
            # issue: stderr cannot be redirect in this form, as a result some failure information
            # is lost when command fails.
            self.exit_code = cli_ctx.invoke(shlex.split(command), out_file=stdout_buf) or 0
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
        except SystemExit as ex:
            # SystemExit not caught by broad exception, check for sys.exit(3)
            if ex.code == 3 and expect_failure:
                self.exit_code = 1
                self.output = stdout_buf.getvalue()
                self.applog = logging_buf.getvalue()
            else:
                raise
        finally:
            stdout_buf.close()
            logging_buf.close()


execute = ExecutionResult
