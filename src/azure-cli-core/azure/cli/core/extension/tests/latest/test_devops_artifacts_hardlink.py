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
        from azure.cli.core.extension import get_extension
        ext = get_extension('azure-devops')
        return ext.path
    except Exception:  # pylint: disable=broad-except
        return None


def _extension_available():
    """Check if the azure-devops extension is installed and importable."""
    ext_path = _get_azure_devops_extension_path()
    if not ext_path:
        return False
    try:
        if ext_path not in sys.path:
            sys.path.insert(0, ext_path)
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

        captured = {}

        def _capture_run(organization, args, message):
            captured['args'] = list(args)
            return None

        with mock.patch.object(invoker, 'run_artifacttool', side_effect=_capture_run):
            invoker.download_universal(**defaults)

        return captured.get('args', [])

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
        invoker = self._make_invoker()
        args = self._run_download_universal(invoker, project='my-project')

        self.assertIn('--project', args)
        self.assertEqual(args[args.index('--project') + 1], 'my-project')
        # Hardlink fallback must still be present even with project scope
        self.assertIn('--allow-hardlink-fallback', args)

    def test_download_universal_with_file_filter(self):
        """download_universal passes --filter when file_filter is specified."""
        invoker = self._make_invoker()
        args = self._run_download_universal(invoker, file_filter='*.txt')

        self.assertIn('--filter', args)
        self.assertEqual(args[args.index('--filter') + 1], '*.txt')
        # Hardlink fallback must still be present even with file filter
        self.assertIn('--allow-hardlink-fallback', args)


if __name__ == '__main__':
    unittest.main()
