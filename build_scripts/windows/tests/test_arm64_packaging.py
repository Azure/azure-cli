# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


class WindowsArm64PackagingTest(unittest.TestCase):

    def test_build_uses_arm64_python_and_wix(self):
        build = (ROOT / 'build_scripts/windows/scripts/build.cmd').read_text()
        project = (ROOT / 'build_scripts/windows/azure-cli.wixproj').read_text(encoding='utf-8-sig')
        self.assertIn('else if "%ARCH%"=="arm64"', build)
        self.assertIn('set PYTHON_ARCH=arm64', build)
        self.assertIn('wix314-binaries.zip', build)
        self.assertIn(
            'WIX_DOWNLOAD_SHA256=6AC824E1642D6F7277D0ED7EA09411A508F6116BA6FAE0AA5F2C7DAA2FF43D31',
            build,
        )
        self.assertIn('Get-FileHash -Algorithm SHA256 wix-archive.zip', build)
        self.assertIn('set WIX_DIR=%ARTIFACTS_DIR%\\wix-3.14.1', build)
        self.assertIn('<LocalWixRoot>artifacts\\wix-3.14.1</LocalWixRoot>', project)

    def test_wix_project_builds_arm64_packages(self):
        project = (ROOT / 'build_scripts/windows/azure-cli.wixproj').read_text(encoding='utf-8-sig')
        solution = (ROOT / 'build_scripts/windows/azure-cli.sln').read_text(encoding='utf-8-sig')
        product = (ROOT / 'build_scripts/windows/Product.wxs').read_text()
        self.assertIn("'Release|arm64'", project)
        self.assertIn('<InstallerPlatform>arm64</InstallerPlatform>', project)
        self.assertIn('Release|arm64 = Release|arm64', solution)
        self.assertIn('$(var.Platform) = "arm64"', product)
        self.assertIn('<?define InstallerVersion = "500" ?>', product)
        self.assertIn('<?define UpgradeCodeArm64', product)

    def test_installation_tests_use_native_program_files(self):
        script = (ROOT / 'build_scripts/windows/scripts/test_msi_installation.ps1').read_text()
        self.assertIn("$env:PLATFORM -eq 'x86'", script)
        self.assertIn('$env:ProgramFiles\\Microsoft SDKs\\Azure\\CLI2', script)

    def test_pipeline_builds_and_tests_arm64_artifacts(self):
        pipeline = (ROOT / 'azure-pipelines.yml').read_text()
        variables = (ROOT / '.azure-pipelines/templates/variables.yml').read_text()
        self.assertIn("windows_arm64_pool: 'pool-windows-2022-arm64'", variables)
        self.assertIn('- name: enableWindowsArm64\n  type: boolean\n  default: false', pipeline)
        self.assertGreaterEqual(pipeline.count('Platform: arm64'), 4)
        self.assertGreaterEqual(
            pipeline.count('PoolName: ${{ variables.windows_arm64_pool }}'), 5
        )
        self.assertGreaterEqual(
            pipeline.count('${{ if eq(parameters.enableWindowsArm64, true) }}:'), 5
        )
        self.assertIn('ArtifactName: msi-$(Platform)', pipeline)
        self.assertIn('ArtifactName: zip-$(Platform)', pipeline)

    def test_unreleased_arm64_dependencies_are_not_pinned(self):
        requirements = (ROOT / 'src/azure-cli/requirements.py3.windows.txt').read_text()
        self.assertIn('cryptography==48.0.1', requirements)
        self.assertIn('psutil==6.1.0', requirements)
        self.assertIn('pyOpenSSL==26.2.0', requirements)
        self.assertNotIn('cryptography==51', requirements)
        self.assertNotIn('pyOpenSSL==26.5', requirements)


if __name__ == '__main__':
    unittest.main()
