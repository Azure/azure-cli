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

import sys
import unittest
from unittest import mock


def _get_azure_devops_extension_path():
    """Find the azure-devops extension path using the CLI extension system."""
    try:
        from azure.cli.core.extension import get_extension, ExtensionNotInstalledException
        ext = get_extension('azure-devops')
        return ext.path
    except (ImportError, ExtensionNotInstalledException, AttributeError):
        return None


def _extension_available():
    """Check if the azure-devops extension is installed and importable."""
    ext_path = _get_azure_devops_extension_path()
    if not ext_path:
        return False
    try:
        if ext_path not in sys.path:
            sys.path.insert(0, ext_path)
        import azext_devops.dev.common.artifacttool  # noqa: F401  # import only to verify availability
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
        ext_path = _get_azure_devops_extension_path()
        if ext_path and ext_path not in sys.path:
            sys.path.insert(0, ext_path)
        from azext_devops.dev.common.artifacttool import ArtifactToolInvoker
        self.ArtifactToolInvoker = ArtifactToolInvoker

    def _make_invoker(self):
        """Create an ArtifactToolInvoker with a mock tool invoker and updater."""
        mock_tool_invoker = mock.MagicMock()
        mock_updater = mock.MagicMock()
        mock_updater.get_latest_artifacttool.return_value = '/mock/artifacttool/path'
        return self.ArtifactToolInvoker(mock_tool_invoker, mock_updater)

    def _run_download_universal(self, invoker, **kwargs):
        """Run download_universal with run_artifacttool mocked to capture args.

        Patches run_artifacttool on the invoker instance to intercept the args list
        before any external calls (credential lookup, binary download, process spawn).
        Returns the args that were passed to run_artifacttool.
        """
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

        with mock.patch.object(invoker, 'run_artifacttool') as mock_run:
            mock_run.return_value = None
            invoker.download_universal(**defaults)

        if mock_run.called:
            # Signature: run_artifacttool(organization, args, message)
            # args is the second positional argument (index 1)
            return list(mock_run.call_args[0][1])
        return []

    def _assert_flag_value(self, args, flag, expected_value):
        """Assert that a flag is present in args and has the expected value immediately after it."""
        self.assertIn(flag, args)
        idx = args.index(flag)
        self.assertLess(idx + 1, len(args), "Flag '{}' has no value after it".format(flag))
        self.assertEqual(args[idx + 1], expected_value)

    def test_download_universal_passes_allow_hardlink_fallback_flag(self):
        """download_universal must pass --allow-hardlink-fallback to the ArtifactTool binary.

        Without this flag, ArtifactTool fails with:
            System.IO.IOException: Hard linking failed! Status: FailedSinceNotSupportedByFilesystem
        on file systems that do not support hard links.
        """
        invoker = self._make_invoker()
        args = self._run_download_universal(invoker)

        self.assertIn(
            '--allow-hardlink-fallback', args,
            "download_universal must pass --allow-hardlink-fallback to ArtifactTool to support "
            "file systems without hard-link support (e.g., ReFS, network shares). "
            "See https://github.com/Azure/azure-cli/issues/32528"
        )

    def test_download_universal_hardlink_fallback_enabled_by_default(self):
        """--allow-hardlink-fallback should be passed by default (no user action required)."""
        invoker = self._make_invoker()
        # Call without specifying allow_hardlink_fallback (should default to True)
        args = self._run_download_universal(invoker)

        self.assertIn('--allow-hardlink-fallback', args)

    def test_download_universal_basic_args_present(self):
        """download_universal passes required --feed, --package-name, --package-version and --path."""
        invoker = self._make_invoker()
        args = self._run_download_universal(
            invoker,
            feed='my-feed',
            package_name='my-pkg',
            package_version='2.3.4',
            path='/downloads',
        )

        self._assert_flag_value(args, '--feed', 'my-feed')
        self._assert_flag_value(args, '--package-name', 'my-pkg')
        self._assert_flag_value(args, '--package-version', '2.3.4')
        self._assert_flag_value(args, '--path', '/downloads')

    def test_download_universal_with_project_scope(self):
        """download_universal passes --project when project is specified."""
        invoker = self._make_invoker()
        args = self._run_download_universal(invoker, project='my-project')

        self._assert_flag_value(args, '--project', 'my-project')
        # Hardlink fallback must still be present even with project scope
        self.assertIn('--allow-hardlink-fallback', args)

    def test_download_universal_with_file_filter(self):
        """download_universal passes --filter when file_filter is specified."""
        invoker = self._make_invoker()
        args = self._run_download_universal(invoker, file_filter='*.txt')

        self._assert_flag_value(args, '--filter', '*.txt')
        # Hardlink fallback must still be present even with file filter
        self.assertIn('--allow-hardlink-fallback', args)


if __name__ == '__main__':
    unittest.main()

