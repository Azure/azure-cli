# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os.path
import unittest
import mock

import azure.cli.core.application as application


class TestVMImage(unittest.TestCase):
    @mock.patch('azure.cli.command_modules.vm.custom.urlopen', autospec=True)
    def test_read_images_from_alias_doc(self, mock_urlopen):
        config = application.Configuration([])
        application.APPLICATION = application.Application(config)
        from azure.cli.command_modules.vm.custom import list_vm_images

        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 'aliases.json')
        with open(file_path, 'r') as test_file:
            test_data = test_file.read().encode()

        mock_read = mock.MagicMock()
        mock_read.read.return_value = test_data
        mock_urlopen.return_value = mock_read

        # action
        images = list_vm_images()

        # assert
        win_images = [i for i in images if i['publisher'] == 'MicrosoftWindowsServer']
        self.assertTrue(len(win_images) > 0)
        ubuntu_image = next(i for i in images if i['publisher'] == 'Canonical')
        self.assertEqual(ubuntu_image['publisher'], 'Canonical')
        self.assertEqual(ubuntu_image['offer'], 'UbuntuServer')
        self.assertEqual(ubuntu_image['urnAlias'], 'UbuntuLTS')
        parts = ubuntu_image['urn'].split(':')
        self.assertEqual(parts[0], ubuntu_image['publisher'])
        self.assertEqual(parts[1], ubuntu_image['offer'])
        self.assertEqual(parts[2], ubuntu_image['sku'])
        self.assertEqual(parts[3], ubuntu_image['version'])


if __name__ == '__main__':
    unittest.main()
