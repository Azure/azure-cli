# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
import importlib

from knack.util import CLIError

acr_import = importlib.import_module('azure.cli.command_modules.acr.import')


class TestSplitRegistryAndImage(unittest.TestCase):

    VALID_ACR_LOGIN_SERVER = 'myregistry.azurecr.io'
    VALID_DOCKER_LOGIN_SERVER = 'docker.io'
    VALID_IMAGE = 'myrepo/myimage:latest'

    VALID_SOURCE_PATTERN = '{}/{}'
    VALID_ACR_SOURCE = VALID_SOURCE_PATTERN.format(VALID_ACR_LOGIN_SERVER, VALID_IMAGE)
    VALID_DOCKER_SOURCE = VALID_SOURCE_PATTERN.format(VALID_DOCKER_LOGIN_SERVER, VALID_IMAGE)

    SINGLE_SLASH = '/'
    SINGLE_DOT = '.'
    EMPTY_SOURCE = ''

    def test_split_valid_acr_source(self):
        login_server, image = acr_import._split_registry_and_image(TestSplitRegistryAndImage.VALID_ACR_SOURCE)
        self.assertEqual((login_server, image), (TestSplitRegistryAndImage.VALID_ACR_LOGIN_SERVER, TestSplitRegistryAndImage.VALID_IMAGE))

    def test_split_valid_docker_source(self):
        login_server, image = acr_import._split_registry_and_image(TestSplitRegistryAndImage.VALID_DOCKER_SOURCE)
        self.assertEqual((login_server, image), (TestSplitRegistryAndImage.VALID_DOCKER_LOGIN_SERVER, TestSplitRegistryAndImage.VALID_IMAGE))

    def test_split_single_login_server(self):
        with self.assertRaises(CLIError):
            acr_import._split_registry_and_image(TestSplitRegistryAndImage.VALID_ACR_LOGIN_SERVER)

    def test_split_single_image(self):
        with self.assertRaises(CLIError):
            acr_import._split_registry_and_image(TestSplitRegistryAndImage.VALID_IMAGE)

    def test_split_single_slash(self):
        with self.assertRaises(CLIError):
            acr_import._split_registry_and_image(TestSplitRegistryAndImage.SINGLE_SLASH)

    def test_split_single_dot(self):
        with self.assertRaises(CLIError):
            acr_import._split_registry_and_image(TestSplitRegistryAndImage.SINGLE_DOT)

    def test_split_empy_source(self):
        with self.assertRaises(CLIError):
            acr_import._split_registry_and_image(TestSplitRegistryAndImage.EMPTY_SOURCE)


if __name__ == '__main__':
    unittest.main()
