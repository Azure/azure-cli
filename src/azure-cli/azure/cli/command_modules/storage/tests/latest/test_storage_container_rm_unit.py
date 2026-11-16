# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from unittest import mock

from azure.cli.core.azclierror import RequiredArgumentMissingError
from azure.mgmt.storage import models

from azure.cli.command_modules.storage.operations.blob import create_container_rm, update_container_rm


class StorageContainerAccessPointTest(unittest.TestCase):

    def setUp(self):
        self.cmd = mock.MagicMock()
        self.cmd.get_models.side_effect = lambda name, **_: getattr(models, name)
        self.client = mock.MagicMock()

    def create(self, **kwargs):
        create_container_rm(self.cmd, self.client, container_name='container',
                            resource_group_name='rg', account_name='storageaccount', **kwargs)
        return self.client.create.call_args.kwargs['blob_container'].as_dict()['properties']

    def test_create_without_attachment_omits_configuration(self):
        self.assertNotIn('blobAccessPointConfiguration', self.create())

    def test_create_attachment_without_unique_id_uses_service_lookup(self):
        properties = self.create(blob_access_point_configuration_name='accesspoint')
        self.assertEqual(
            {'blobAccessPointConfigurationName': 'accesspoint'}, properties['blobAccessPointConfiguration'])

    def test_create_attachment_with_unique_id(self):
        unique_id = '00000000-0000-0000-0000-000000000001'
        properties = self.create(blob_access_point_configuration_name='accesspoint',
                                 blob_access_point_configuration_unique_id=unique_id)
        self.assertEqual({
            'blobAccessPointConfigurationName': 'accesspoint',
            'blobAccessPointConfigurationUniqueId': unique_id
        }, properties['blobAccessPointConfiguration'])

    def test_unique_id_requires_configuration_name(self):
        with self.assertRaisesRegex(RequiredArgumentMissingError, '--blob-access-point-configuration-name'):
            self.create(blob_access_point_configuration_unique_id='00000000-0000-0000-0000-000000000001')
        self.client.create.assert_not_called()

    def test_update_does_not_resend_create_only_attachment(self):
        instance = models.BlobContainer(
            metadata={'key': 'value'},
            blob_access_point_configuration=models.BlobAccessPointConfigurationConnection(
                blob_access_point_configuration_name='accesspoint'))
        properties = update_container_rm(self.cmd, instance).as_dict()['properties']
        self.assertEqual({'key': 'value'}, properties['metadata'])
        self.assertNotIn('blobAccessPointConfiguration', properties)
