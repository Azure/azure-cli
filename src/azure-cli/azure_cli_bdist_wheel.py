# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

from setuptools.command.build_py import build_py


class azure_cli_build_py(build_py):

    def initialize_options(self):
        super().initialize_options()
        self.extra_build_source_files = None

    def build_packages(self):
        super().build_packages()
        if self.extra_build_source_files:
            for source in self.extra_build_source_files.strip().splitlines():
                package, module, module_file = source.strip().split(',')
                self.build_module(module, module_file, package)


cmdclass = {
    'build_py': azure_cli_build_py,
}
