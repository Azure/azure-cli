# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[3]


class WindowsArm64PackagingTest(unittest.TestCase):

    def test_build_uses_arm64_python_and_wix(self):
        build = (ROOT / 'build_scripts/windows/scripts/build.cmd').read_text()
        self.assertIn('else if "%ARCH%"=="arm64"', build)
        self.assertIn('set PYTHON_ARCH=arm64', build)
        self.assertIn('wix314-binaries.zip', build)

    def test_wix_project_builds_arm64_packages(self):
        project = (ROOT / 'build_scripts/windows/azure-cli.wixproj').read_text(encoding='utf-8-sig')
        product = (ROOT / 'build_scripts/windows/Product.wxs').read_text()
        self.assertIn("'Release|arm64'", project)
        self.assertIn('<InstallerPlatform>arm64</InstallerPlatform>', project)
        self.assertIn('$(var.Platform) = "arm64"', product)
        self.assertIn('<?define InstallerVersion = "500" ?>', product)
        self.assertIn('<?define UpgradeCodeArm64', product)

    def test_installation_tests_use_native_program_files(self):
        script = (ROOT / 'build_scripts/windows/scripts/test_msi_installation.ps1').read_text()
        self.assertIn("$env:PLATFORM -eq 'x86'", script)
        self.assertIn('$env:ProgramFiles\\Microsoft SDKs\\Azure\\CLI2', script)


if __name__ == '__main__':
    unittest.main()
