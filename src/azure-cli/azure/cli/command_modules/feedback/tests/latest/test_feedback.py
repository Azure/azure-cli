# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import datetime
import logging
import os
import time
import unittest
from unittest import mock
from knack.events import EVENT_CLI_POST_EXECUTE

from azure.cli.core.azlogging import CommandLoggerContext
from azure.cli.core.extension.operations import get_extensions, add_extension, remove_extension, WheelExtension
from azure.cli.command_modules.feedback.custom import (_get_command_log_files, _build_issue_info_tup,
                                                       _get_extension_repo_url, _CLI_ISSUES_URL,
                                                       _is_valid_github_project_url,
                                                       _EXTENSIONS_ISSUES_URL, _RAW_EXTENSIONS_ISSUES_URL)
from azure.cli.core.commands import AzCliCommand

from azure.cli.testsdk import ScenarioTest
from azure.cli.testsdk.base import execute
from azure.cli.testsdk.reverse_dependency import get_dummy_cli

# pylint: disable=line-too-long
# pylint: disable=too-many-lines

logger = logging.getLogger(__name__)


class TestCommandLogFile(ScenarioTest):

    def __init__(self, *args, **kwargs):
        super(TestCommandLogFile, self).__init__(*args, **kwargs)

        self.disable_recording = True
        self.is_live = True

    # using setup to benefit from self.cmd(). There should be only one test fixture in this class
    def setUp(self):
        def _add_alias(self, command_log_dir, logger):
            self.cli_ctx.logging.command_log_dir = command_log_dir
            self.cmd("az extension add -n alias")
            logger.warning("Adding whl ext alias")

        super(TestCommandLogFile, self).setUp()
        self.temp_command_log_dir = self.create_temp_dir()

        # if alias is installed as a wheel extension. Remove it for now and re-install it later.
        if "alias" in [ext.name for ext in get_extensions() if isinstance(ext, WheelExtension)]:
            logger.warning("Removing whl ext alias, will reinstall it afterwards if it is a published whl extension.")
            self.cmd("az extension remove -n alias")
            self.addCleanup(_add_alias, self, self.cli_ctx.logging.command_log_dir, logger)

        self.cli_ctx.logging.command_log_dir = self.temp_command_log_dir

        # populate command dir with logs
        self._run_cmd("extension remove -n alias", expect_failure=True)
        time.sleep(2)
        self._run_cmd("extension add -n alias")
        time.sleep(2)
        self._run_cmd("alias create -n foo123 -c bar123", expect_failure=True)
        time.sleep(2)
        self._run_cmd("alias list")

    # There must be only one test fixture for this class. This is because the commands in setup must be run only once.
    def test_feedback(self):
        self._helper_test_log_metadata_correct()
        self._helper_test_log_contents_correct()
        self._helper_test_build_issue_info()
        self._helper_test_get_repository_url_pretty()
        self._helper_test_get_repository_url_raw()
        self._helper_test_get_repository_url_with_no_extension_match_pretty()
        self._helper_test_get_repository_url_with_no_extension_match_raw()
        self._helper_test_is_valid_github_project_url()

    def _helper_test_is_valid_github_project_url(self):
        self.assertTrue(_is_valid_github_project_url('https://github.com/azure/devops-extension'))
        self.assertFalse(_is_valid_github_project_url('https://github.com/'))
        self.assertFalse(_is_valid_github_project_url('https://github.com/Azure/azure-cli-extensions/tree/master/src/vm-repair'))
        self.assertFalse(_is_valid_github_project_url('https://docs.microsoft.com/azure/machine-learning/service/'))

    def _helper_test_get_repository_url_pretty(self):
        # default behaviour is pretty url
        repo_url = _get_extension_repo_url('alias')
        self.assertEqual(_EXTENSIONS_ISSUES_URL, repo_url)

    def _helper_test_get_repository_url_raw(self):
        repo_url = _get_extension_repo_url('alias', raw=True)
        self.assertEqual(_RAW_EXTENSIONS_ISSUES_URL, repo_url)

    def _helper_test_get_repository_url_with_no_extension_match_pretty(self):
        # default behaviour is pretty url
        repo_url = _get_extension_repo_url('wrong_ext_name')
        self.assertEqual(_EXTENSIONS_ISSUES_URL, repo_url)

    def _helper_test_get_repository_url_with_no_extension_match_raw(self):
        # default behaviour is pretty url
        repo_url = _get_extension_repo_url('wrong_ext_name', raw=True)
        self.assertEqual(_RAW_EXTENSIONS_ISSUES_URL, repo_url)

    def _helper_test_log_metadata_correct(self):
        time_now = datetime.datetime.now()
        command_log_files = _get_command_log_files(self.cli_ctx, time_now)
        p_id = os.getpid()
        self.assertEqual(len(command_log_files), 4)

        for log_file in command_log_files:
            path = log_file.metadata_tup.file_path
            time_ago = log_file.metadata_tup.seconds_ago

            # time of logging should be within a couple minutes of this check
            self.assertTrue(time_ago < 300)
            self.assertEqual(log_file.metadata_tup.p_id, p_id)
            self.assertTrue(os.path.basename(path), self.temp_command_log_dir)
            self.assertEqual(log_file.metadata_tup.cmd, log_file.get_command_name_str())

        self.assertEqual("az extension remove", command_log_files[0].metadata_tup.cmd)
        self.assertEqual("az extension add", command_log_files[1].metadata_tup.cmd)
        self.assertEqual("az alias create", command_log_files[2].metadata_tup.cmd)
        self.assertEqual("az alias list", command_log_files[3].metadata_tup.cmd)

    def _helper_test_log_contents_correct(self):
        time_now = datetime.datetime.now()
        command_log_files = _get_command_log_files(self.cli_ctx, time_now)
        self.assertEqual(len(command_log_files), 4)

        self.assertEqual(command_log_files[0].get_command_status(), "FAILURE")
        self.assertEqual(command_log_files[1].get_command_status(), "SUCCESS")
        self.assertEqual(command_log_files[2].get_command_status(), "FAILURE")
        self.assertEqual(command_log_files[3].get_command_status(), "SUCCESS")

        was_successful = command_log_files[0].command_data_dict.pop("success")
        self.assertEqual(command_log_files[0].get_command_status(), "RUNNING")
        command_log_files[0].command_data_dict["success"] = was_successful

        # check failed cli command:
        data_dict = command_log_files[0].command_data_dict
        self.assertTrue(data_dict["success"] is False)
        self.assertEqual("The extension alias is not installed.", data_dict["errors"][0].strip())
        self.assertEqual(data_dict["command_args"], "extension remove -n {}")

        # check successful cli command
        data_dict = command_log_files[1].command_data_dict
        self.assertTrue(data_dict["success"] is True)
        self.assertEqual(data_dict["command_args"], "extension add -n {}")

        # check unsuccessful extension command
        data_dict = command_log_files[2].command_data_dict
        self.assertTrue(data_dict["success"] is False)
        self.assertTrue("errors" in data_dict)
        self.assertEqual(data_dict["command_args"], "alias create -n {} -c {}")

        # check successful extension command
        data_dict = command_log_files[3].command_data_dict
        self.assertTrue(data_dict["success"] is True)
        self.assertEqual(data_dict["command_args"], "alias list")

        ext_version = self.cmd("az extension show -n alias").get_output_in_json()["version"]
        for i, log_file in enumerate(command_log_files):
            if i >= 2:
                self.assertEqual(data_dict["extension_name"], "alias")
                self.assertEqual(data_dict["extension_version"], ext_version)

    def _helper_test_build_issue_info(self):
        items = []
        command_log_files = _get_command_log_files(self.cli_ctx)

        log_file = command_log_files[0]
        issue_prefix, _, original_issue_body = _build_issue_info_tup(log_file)
        items.append((log_file, original_issue_body))
        self.assertTrue(_CLI_ISSUES_URL in issue_prefix)

        log_file = command_log_files[2]
        issue_prefix, _, original_issue_body = _build_issue_info_tup(log_file)
        items.append((log_file, original_issue_body))
        self.assertTrue(_EXTENSIONS_ISSUES_URL in issue_prefix)
        self.assertTrue(log_file.command_data_dict["extension_name"] in original_issue_body)
        self.assertTrue(log_file.command_data_dict["extension_version"] in original_issue_body)

        for log_file, original_issue_body in items:
            self.assertTrue(log_file.get_command_name_str() in original_issue_body)
            self.assertTrue(log_file.command_data_dict["command_args"] in original_issue_body)
            self.assertTrue(log_file.command_data_dict["errors"][0] in original_issue_body)

    @staticmethod
    def _ext_installed(ext):
        return ext in [ext.name for ext in get_extensions()]

    def _run_cmd(self, command, checks=None, expect_failure=False):
        cli_ctx = get_dummy_cli()
        cli_ctx.logging.command_log_dir = self.temp_command_log_dir

        # azure.cli.core.util.handle_exception is mocked by azure.cli.testsdk.patches.patch_main_exception_handler
        # Patch it again so that errors are properly written to command log file.
        from azure.cli.core.util import handle_exception
        original_handle_exception = handle_exception

        def _handle_exception_with_log(ex, *args, **kwargs):
            with CommandLoggerContext(logger):
                logger.error(ex)
            original_handle_exception(*args, **kwargs)

        with mock.patch('azure.cli.core.util.handle_exception', _handle_exception_with_log):
            result = execute(cli_ctx, command, expect_failure=expect_failure).assert_with_checks(checks)
        return result


if __name__ == '__main__':
    unittest.main()
