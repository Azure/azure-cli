# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
import importlib

from knack.util import CLIError

# The path contains a reserved keyword 'import', so we need a workaround here
acr_import = importlib.import_module('azure.cli.command_modules.acr.import')


class TestSplitRegistryAndImage(unittest.TestCase):

    def test_split_valid_acr_source(self):
        valid_acr_source = 'myregistry.azurecr.io/myrepo/myimage:latest'
        login_server, image = acr_import._split_registry_and_image(valid_acr_source)
        self.assertEqual((login_server, image), ('myregistry.azurecr.io', 'myrepo/myimage:latest'))

    def test_split_valid_docker_source(self):
        valid_docker_source = 'docker.io/myrepo/myimage:latest'
        login_server, image = acr_import._split_registry_and_image(valid_docker_source)
        self.assertEqual((login_server, image), ('docker.io', 'myrepo/myimage:latest'))

    def test_split_single_login_server(self):
        single_login_server = 'myregistry.azurecr.io'
        with self.assertRaises(CLIError):
            acr_import._split_registry_and_image(single_login_server)

    def test_split_single_image(self):
        single_image = 'myrepo/myimage:latest'
        with self.assertRaises(CLIError):
            acr_import._split_registry_and_image(single_image)

    def test_split_single_slash(self):
        single_slash = '/'
        with self.assertRaises(CLIError):
            acr_import._split_registry_and_image(single_slash)

    def test_split_single_dot(self):
        single_dot = '.'
        with self.assertRaises(CLIError):
            acr_import._split_registry_and_image(single_dot)

    def test_split_empy_source(self):
        empty_source = ''
        with self.assertRaises(CLIError):
            acr_import._split_registry_and_image(empty_source)
