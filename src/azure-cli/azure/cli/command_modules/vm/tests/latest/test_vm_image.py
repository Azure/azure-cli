# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os.path
import unittest
from unittest import mock

from azure.cli.core.cloud import CloudEndpointNotSetException
from azure.cli.core.mock import DummyCli

from knack.util import CLIError


def _get_test_cmd():
    from azure.cli.core.mock import DummyCli
    from azure.cli.core import AzCommandsLoader
    from azure.cli.core.commands import AzCliCommand
    from azure.cli.core.profiles import ResourceType
    cli_ctx = DummyCli()
    loader = AzCommandsLoader(cli_ctx, resource_type=ResourceType.MGMT_COMPUTE)
    cmd = AzCliCommand(loader, 'test', None)
    cmd.command_kwargs = {'resource_type': ResourceType.MGMT_COMPUTE}
    cmd.cli_ctx = cli_ctx
    return cmd


class TestVMImage(unittest.TestCase):

    def test_read_images_from_alias_doc(self):
        from azure.cli.command_modules.vm.custom import list_vm_images
        cmd = _get_test_cmd()

        # action
        images = list_vm_images(cmd)

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

    @mock.patch('azure.cli.core.cloud.get_active_cloud', autospec=True)
    def test_when_alias_doc_is_missing(self, mock_get_active_cloud):
        from azure.cli.command_modules.vm._actions import load_images_from_aliases_doc
        p = mock.PropertyMock(side_effect=CloudEndpointNotSetException(''))
        mock_cloud = mock.MagicMock()
        type(mock_cloud.endpoints).vm_image_alias_doc = p
        mock_get_active_cloud.return_value = mock_cloud
        # assert
        cli_ctx = DummyCli()
        cli_ctx.cloud = mock_cloud
        images = load_images_from_aliases_doc(cli_ctx)
        self.assertEqual(images[0], {'urnAlias': 'CentOS', 'publisher': 'OpenLogic',
                                     'offer': 'CentOS', 'sku': '7.5', 'version': 'latest',
                                     'architecture': 'x64'})


if __name__ == '__main__':
    unittest.main()
