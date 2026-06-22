# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
Tests to ensure az artifacts universal download passes --allow-hardlink-fallback
to ArtifactTool, fixing failures on file systems that do not support hard linking
(e.g., ReFS volumes, network shares, Docker containers).

See: https://github.com/Azure/azure-cli/issues/32528
"""

import os
import sys
import unittest
from unittest import mock


AZURE_DEVOPS_EXT_PATH = '/opt/az/azcliextensions/azure-devops'


def _extension_available():
    """Check if the azure-devops extension is installed and importable."""
    if not os.path.isdir(AZURE_DEVOPS_EXT_PATH):
        return False
    try:
        if AZURE_DEVOPS_EXT_PATH not in sys.path:
            sys.path.insert(0, AZURE_DEVOPS_EXT_PATH)
        import azext_devops.dev.common.artifacttool  # noqa: F401
        return True
    except ImportError:
        return False


@unittest.skipUnless(_extension_available(), "azure-devops extension not installed")
class TestArtifactToolHardlinkFallback(unittest.TestCase):
    """Regression tests for az artifacts universal download on file systems without hard-link support.

    The ArtifactTool binary uses hard links by default when downloading package files.
    On file systems that do not support hard linking (e.g., ReFS on Windows, certain Linux
    filesystems, network shares), this causes the tool to exit with a non-zero return code
    and the error:
        System.IO.IOException: Hard linking failed!
        Status: FailedSinceNotSupportedByFilesystem

    The fix is to always pass --allow-hardlink-fallback to ArtifactTool when downloading.
    This flag instructs ArtifactTool to fall back to a regular file copy if hard linking fails,
    so downloads succeed on all file systems.
    """

    def setUp(self):
        if AZURE_DEVOPS_EXT_PATH not in sys.path:
            sys.path.insert(0, AZURE_DEVOPS_EXT_PATH)
        from azext_devops.dev.common.artifacttool import ArtifactToolInvoker
        self.ArtifactToolInvoker = ArtifactToolInvoker

    def _make_invoker(self):
        """Create an ArtifactToolInvoker with a mock tool invoker and updater."""
        mock_tool_invoker = mock.MagicMock()
        mock_updater = mock.MagicMock()
        mock_updater.get_latest_artifacttool.return_value = '/mock/artifacttool/path'
        return self.ArtifactToolInvoker(mock_tool_invoker, mock_updater), mock_tool_invoker

    def _get_captured_args(self, mock_tool_invoker):
        """Extract the command args from the mock tool invoker's run call."""
        call_args = mock_tool_invoker.run.call_args
        if call_args is None:
            return []
        return call_args[0][0]  # First positional arg is command_args list

    def _run_download_universal(self, invoker, **kwargs):
        """Run download_universal with mocked credentials."""
        defaults = dict(
            organization='https://dev.azure.com/TestOrg/',
            project=None,
            feed='test-feed',
            package_name='test-package',
            package_version='1.0.0',
            path='/tmp/test-download',
            file_filter=None,
        )
        defaults.update(kwargs)

        mock_run_result = mock.MagicMock()
        mock_run_result.stdout.read.return_value = b'{}'
        invoker._tool_invoker.run.return_value = mock_run_result

        with mock.patch('azext_devops.dev.common.artifacttool._get_credentials') as mock_creds:
            mock_creds.return_value = mock.MagicMock(password='test-pat')
            invoker.download_universal(**defaults)

    def test_download_universal_passes_allow_hardlink_fallback_flag(self):
        """download_universal must pass --allow-hardlink-fallback to the ArtifactTool binary.

        Without this flag, ArtifactTool fails with:
            System.IO.IOException: Hard linking failed! Status: FailedSinceNotSupportedByFilesystem
        on file systems that do not support hard links.
        """
        invoker, mock_tool_invoker = self._make_invoker()
        self._run_download_universal(invoker)

        args = self._get_captured_args(mock_tool_invoker)
        self.assertIn(
            '--allow-hardlink-fallback', args,
            "download_universal must pass --allow-hardlink-fallback to ArtifactTool to support "
            "file systems without hard-link support (e.g., ReFS, network shares). "
            "See https://github.com/Azure/azure-cli/issues/32528"
        )

    def test_download_universal_hardlink_fallback_enabled_by_default(self):
        """--allow-hardlink-fallback should be passed by default (no user action required)."""
        invoker, mock_tool_invoker = self._make_invoker()
        # Call without specifying allow_hardlink_fallback (should default to True)
        self._run_download_universal(invoker)

        args = self._get_captured_args(mock_tool_invoker)
        self.assertIn('--allow-hardlink-fallback', args)

    def test_download_universal_basic_args_present(self):
        """download_universal passes required --feed, --package-name, --package-version and --path."""
        invoker, mock_tool_invoker = self._make_invoker()
        self._run_download_universal(
            invoker,
            feed='my-feed',
            package_name='my-pkg',
            package_version='2.3.4',
            path='/downloads',
        )

        args = self._get_captured_args(mock_tool_invoker)
        self.assertIn('--feed', args)
        self.assertEqual(args[args.index('--feed') + 1], 'my-feed')
        self.assertIn('--package-name', args)
        self.assertEqual(args[args.index('--package-name') + 1], 'my-pkg')
        self.assertIn('--package-version', args)
        self.assertEqual(args[args.index('--package-version') + 1], '2.3.4')
        self.assertIn('--path', args)
        self.assertEqual(args[args.index('--path') + 1], '/downloads')

    def test_download_universal_with_project_scope(self):
        """download_universal passes --project when project is specified."""
        invoker, mock_tool_invoker = self._make_invoker()
        self._run_download_universal(invoker, project='my-project')

        args = self._get_captured_args(mock_tool_invoker)
        self.assertIn('--project', args)
        self.assertEqual(args[args.index('--project') + 1], 'my-project')
        # Hardlink fallback must still be present even with project scope
        self.assertIn('--allow-hardlink-fallback', args)

    def test_download_universal_with_file_filter(self):
        """download_universal passes --filter when file_filter is specified."""
        invoker, mock_tool_invoker = self._make_invoker()
        self._run_download_universal(invoker, file_filter='*.txt')

        args = self._get_captured_args(mock_tool_invoker)
        self.assertIn('--filter', args)
        self.assertEqual(args[args.index('--filter') + 1], '*.txt')
        # Hardlink fallback must still be present even with file filter
        self.assertIn('--allow-hardlink-fallback', args)


if __name__ == '__main__':
    unittest.main()
