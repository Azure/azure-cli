# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

from setuptools.command.build_py import build_py


class azure_cli_build_py(build_py):

    def initialize_options(self):
        super(azure_cli_build_py, self).initialize_options()
        self.extra_build_source_files = None

    def build_packages(self):
        super(azure_cli_build_py, self).build_packages()
        if self.extra_build_source_files:
            package, module, module_file = self.extra_build_source_files.split(',')
            self.build_module(module, module_file, package)


cmdclass = {
    'build_py': azure_cli_build_py,
}
