# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from unittest.mock import patch, MagicMock

from knack.util import CLIError


class TestArtifactsUniversal(unittest.TestCase):

    _TEST_ORGANIZATION = 'https://dev.azure.com/myorg/'
    _TEST_PROJECT = 'my-project'
    _TEST_FEED = 'my-feed'
    _TEST_PACKAGE_NAME = 'my-package'
    _TEST_PACKAGE_VERSION = '1.0.0'
    _TEST_PATH = './output'
    _TEST_FILTER = '*.txt'
    _TEST_DESCRIPTION = 'test description'

    def setUp(self):
        self.patcher_run = patch(
            'azure.cli.command_modules.devops._artifacttool.ArtifactToolInvoker._run_artifacttool'
        )
        self.mock_run = self.patcher_run.start()
        self.mock_run.return_value = None

        self.patcher_get_dir = patch(
            'azure.cli.command_modules.devops._artifacttool._get_artifacttool_dir'
        )
        self.mock_get_dir = self.patcher_get_dir.start()
        self.mock_get_dir.return_value = '/mock/artifacttool/dir'

        self.patcher_get_pat = patch(
            'azure.cli.command_modules.devops._artifacttool._get_pat'
        )
        self.mock_get_pat = self.patcher_get_pat.start()
        self.mock_get_pat.return_value = 'mock-token'

    def tearDown(self):
        self.patcher_run.stop()
        self.patcher_get_dir.stop()
        self.patcher_get_pat.stop()

    # ---- download_package tests ----

    def test_download_package_passes_no_hardlinks_flag(self):
        """Verify that --no-hardlinks is passed to ArtifactTool when the flag is set."""
        from azure.cli.command_modules.devops.custom import download_package
        download_package(
            feed=self._TEST_FEED,
            name=self._TEST_PACKAGE_NAME,
            version=self._TEST_PACKAGE_VERSION,
            path=self._TEST_PATH,
            no_hardlinks=True,
            organization=self._TEST_ORGANIZATION,
        )
        self.mock_run.assert_called_once()
        args = self.mock_run.call_args[0][1]
        self.assertIn('--no-hardlinks', args)

    def test_download_package_without_no_hardlinks_flag(self):
        """Verify that --no-hardlinks is NOT passed when the flag is not set."""
        from azure.cli.command_modules.devops.custom import download_package
        download_package(
            feed=self._TEST_FEED,
            name=self._TEST_PACKAGE_NAME,
            version=self._TEST_PACKAGE_VERSION,
            path=self._TEST_PATH,
            no_hardlinks=False,
            organization=self._TEST_ORGANIZATION,
        )
        self.mock_run.assert_called_once()
        args = self.mock_run.call_args[0][1]
        self.assertNotIn('--no-hardlinks', args)

    def test_download_package_with_project_scope(self):
        """Verify project scope download includes --project."""
        from azure.cli.command_modules.devops.custom import download_package
        download_package(
            feed=self._TEST_FEED,
            name=self._TEST_PACKAGE_NAME,
            version=self._TEST_PACKAGE_VERSION,
            path=self._TEST_PATH,
            scope='project',
            organization=self._TEST_ORGANIZATION,
            project=self._TEST_PROJECT,
        )
        self.mock_run.assert_called_once()
        args = self.mock_run.call_args[0][1]
        self.assertIn('--project', args)
        self.assertIn(self._TEST_PROJECT, args)

    def test_download_package_with_file_filter(self):
        """Verify file filter is passed to ArtifactTool."""
        from azure.cli.command_modules.devops.custom import download_package
        download_package(
            feed=self._TEST_FEED,
            name=self._TEST_PACKAGE_NAME,
            version=self._TEST_PACKAGE_VERSION,
            path=self._TEST_PATH,
            file_filter=self._TEST_FILTER,
            organization=self._TEST_ORGANIZATION,
        )
        self.mock_run.assert_called_once()
        args = self.mock_run.call_args[0][1]
        self.assertIn('--filter', args)
        self.assertIn(self._TEST_FILTER, args)

    def test_download_package_project_without_scope_raises_error(self):
        """Verify that specifying --project without --scope project raises CLIError."""
        from azure.cli.command_modules.devops.custom import download_package
        with self.assertRaises(CLIError) as ctx:
            download_package(
                feed=self._TEST_FEED,
                name=self._TEST_PACKAGE_NAME,
                version=self._TEST_PACKAGE_VERSION,
                path=self._TEST_PATH,
                organization=self._TEST_ORGANIZATION,
                project=self._TEST_PROJECT,  # scope defaults to 'organization'
            )
        self.assertIn('--scope', str(ctx.exception))

    def test_download_package_args_structure(self):
        """Verify the full argument structure passed to ArtifactTool for download."""
        from azure.cli.command_modules.devops.custom import download_package
        from azure.cli.command_modules.devops._artifacttool import ARTIFACTTOOL_PAT_ENVKEY
        download_package(
            feed=self._TEST_FEED,
            name=self._TEST_PACKAGE_NAME,
            version=self._TEST_PACKAGE_VERSION,
            path=self._TEST_PATH,
            organization=self._TEST_ORGANIZATION,
        )
        args = self.mock_run.call_args[0][1]
        self.assertIn('universal', args)
        self.assertIn('download', args)
        self.assertIn('--service', args)
        self.assertIn(self._TEST_ORGANIZATION, args)
        self.assertIn('--patvar', args)
        self.assertIn(ARTIFACTTOOL_PAT_ENVKEY, args)
        self.assertIn('--feed', args)
        self.assertIn(self._TEST_FEED, args)
        self.assertIn('--package-name', args)
        self.assertIn(self._TEST_PACKAGE_NAME, args)
        self.assertIn('--package-version', args)
        self.assertIn(self._TEST_PACKAGE_VERSION, args)
        self.assertIn('--path', args)
        self.assertIn(self._TEST_PATH, args)

    # ---- publish_package tests ----

    def test_publish_package_args_structure(self):
        """Verify the full argument structure passed to ArtifactTool for publish."""
        from azure.cli.command_modules.devops.custom import publish_package
        from azure.cli.command_modules.devops._artifacttool import ARTIFACTTOOL_PAT_ENVKEY
        publish_package(
            feed=self._TEST_FEED,
            name=self._TEST_PACKAGE_NAME,
            version=self._TEST_PACKAGE_VERSION,
            path=self._TEST_PATH,
            organization=self._TEST_ORGANIZATION,
        )
        args = self.mock_run.call_args[0][1]
        self.assertIn('universal', args)
        self.assertIn('publish', args)
        self.assertIn('--service', args)
        self.assertIn('--patvar', args)
        self.assertIn(ARTIFACTTOOL_PAT_ENVKEY, args)
        self.assertIn('--feed', args)
        self.assertIn('--package-name', args)
        self.assertIn('--package-version', args)
        self.assertIn('--path', args)

    def test_publish_package_with_description(self):
        """Verify description is passed to ArtifactTool."""
        from azure.cli.command_modules.devops.custom import publish_package
        publish_package(
            feed=self._TEST_FEED,
            name=self._TEST_PACKAGE_NAME,
            version=self._TEST_PACKAGE_VERSION,
            path=self._TEST_PATH,
            description=self._TEST_DESCRIPTION,
            organization=self._TEST_ORGANIZATION,
        )
        args = self.mock_run.call_args[0][1]
        self.assertIn('--description', args)
        self.assertIn(self._TEST_DESCRIPTION, args)

    def test_publish_package_with_project_scope(self):
        """Verify project scope publish includes --project."""
        from azure.cli.command_modules.devops.custom import publish_package
        publish_package(
            feed=self._TEST_FEED,
            name=self._TEST_PACKAGE_NAME,
            version=self._TEST_PACKAGE_VERSION,
            path=self._TEST_PATH,
            scope='project',
            organization=self._TEST_ORGANIZATION,
            project=self._TEST_PROJECT,
        )
        args = self.mock_run.call_args[0][1]
        self.assertIn('--project', args)
        self.assertIn(self._TEST_PROJECT, args)

    def test_publish_package_project_without_scope_raises_error(self):
        """Verify that specifying --project without --scope project raises CLIError."""
        from azure.cli.command_modules.devops.custom import publish_package
        with self.assertRaises(CLIError) as ctx:
            publish_package(
                feed=self._TEST_FEED,
                name=self._TEST_PACKAGE_NAME,
                version=self._TEST_PACKAGE_VERSION,
                path=self._TEST_PATH,
                organization=self._TEST_ORGANIZATION,
                project=self._TEST_PROJECT,  # scope defaults to 'organization'
            )
        self.assertIn('--scope', str(ctx.exception))


if __name__ == '__main__':
    unittest.main()
