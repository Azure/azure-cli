# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import time
from azure.cli.testsdk import ScenarioTest,ResourceGroupPreparer


class TestDevice(ScenarioTest):

    @ResourceGroupPreparer(key='rg')
    def test_device(self):
        tag_key = self.create_random_name(prefix='key-', length=10)
        tag_value = self.create_random_name(prefix='val-', length=10)

        self.kwargs.update({
            'name': self.create_random_name(prefix='cli-', length=20),
            'sku': 'Gateway',
            'location': 'eastus',
            'tags': tag_key + '=' + tag_value,
        })

        device = self.cmd('databoxedge device create -l {location} --sku {sku} --name {name} -g {rg}', checks=[
            self.check('name', '{name}'),
            self.check('resourceGroup', '{rg}'),
            self.check('deviceType', 'DataBoxEdgeDevice'),
            self.check('sku.name', '{sku}'),
            self.check('sku.tier', 'Standard'),
            self.check('location', '{location}')
        ]).get_output_in_json()

        self.cmd('databoxedge device update --name {name} -g {rg} --tags {tags}', checks=[
            self.check('id', device['id']),
            self.check('name', '{name}'),
            self.check('resourceGroup', '{rg}'),
            self.check('tags', {tag_key: tag_value})
        ])

        self.cmd('databoxedge device list -g {rg}', checks=[
            self.check('length(@)', 1),
            self.check('type(@)', 'array'),
            self.check('[0].id', device['id']),
            self.check('[0].name', '{name}'),
            self.check('[0].resourceGroup', '{rg}'),
            self.check('[0].tags', {tag_key: tag_value})
        ])

        self.cmd('databoxedge device show -n {name} -g {rg}', checks=[
            self.check('name', '{name}'),
            self.check('resourceGroup', '{rg}'),
            self.check('deviceType', 'DataBoxEdgeDevice'),
            self.check('sku.name', '{sku}'),
            self.check('sku.tier', 'Standard'),
            self.check('location', '{location}'),
            self.check('tags', {tag_key: tag_value})
        ])

        self.cmd('databoxedge device show-update-summary -n {name} -g {rg}', checks=[
            self.check('name', 'default'),
            self.check('resourceGroup', '{rg}')
        ])
        self.cmd('databoxedge alert list -d {name} -g {rg}', checks=self.is_empty())
        self.cmd('databoxedge list-node -g {rg} -d {name}', checks=self.is_empty())
        self.cmd('databoxedge device delete -n {name} -g {rg} -y')
        time.sleep(30)
        self.cmd('databoxedge device list -g {rg}', checks=[self.is_empty()])

    def test_device_subresource(self):
        self.kwargs.update({
            'share_name': self.create_random_name('share', 10),
            'container_name': self.create_random_name('container', 15)
        })
        self.cmd('az databoxedge device share create -g databoxedge_test -n {share_name} --device-name testdevice1 --access-protocol NFS --monitoring-status Enabled --share-status OK --azure-container-info {{containerName:{container_name},dataFormat:BlockBlob,storageAccountCredentialId:/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/databoxedge_test/providers/Microsoft.DataBoxEdge/dataBoxEdgeDevices/testedgedevice/storageAccountCredentials/asekvlogsase03cf9b66edfc}}', checks=[
            self.check('name', '{share_name}'),
            self.check('accessProtocol', 'NFS'),
            self.check('azureContainerInfo.containerName', '{container_name}'),
            self.check('shareStatus', 'OK')
        ])
        self.cmd('az databoxedge device share update -g databoxedge_test -n {share_name} --device-name testdevice1 --description test', checks=[
            self.check('name', '{share_name}'),
            self.check('accessProtocol', 'NFS'),
            self.check('azureContainerInfo.containerName', '{container_name}'),
            self.check('shareStatus', 'OK'),
            self.check('description', 'test')
        ])
        self.cmd('az databoxedge device share show -g databoxedge_test -n {share_name} --device-name testdevice1', checks=[
            self.check('name', '{share_name}'),
            self.check('accessProtocol', 'NFS'),
            self.check('azureContainerInfo.containerName', '{container_name}'),
            self.check('shareStatus', 'OK'),
            self.check('description', 'test')
        ])
        self.cmd('az databoxedge device share list -g databoxedge_test --device-name testdevice1', checks=[
            self.check('[0].type', 'Microsoft.DataBoxEdge/dataBoxEdgeDevices/shares'),
            self.check('[0].shareStatus', 'OK'),
        ])

        self.cmd('az databoxedge device user list -g databoxedge_test --device-name testdevice1', checks=[
            self.check('[0].type', 'Microsoft.DataBoxEdge/dataBoxEdgeDevices/users'),
            self.check('[0].userType', 'Share')
        ])
        self.cmd('az databoxedge device user show -g databoxedge_test -n testshare1 --device-name testdevice1', checks=[
            self.check('name', 'testshare1'),
            self.check('type', 'Microsoft.DataBoxEdge/dataBoxEdgeDevices/users'),
            self.check('userType', 'Share')
        ])

        self.cmd('az databoxedge device storage-account-credential list -g databoxedge_test --device-name testdevice1', checks=[
            self.check('[0].type', 'Microsoft.DataBoxEdge/dataBoxEdgeDevices/storageAccountCredentials')
        ])
        self.cmd('az databoxedge device storage-account-credential show -g databoxedge_test -n sac1 --device-name testdevice1', checks=[
            self.check('name', 'sac1'),
            self.check('type', 'Microsoft.DataBoxEdge/dataBoxEdgeDevices/storageAccountCredentials'),
            self.check('accountType', 'BlobStorage')
        ])

        self.cmd('az databoxedge device storage-account list -g databoxedge_test --device-name testdevice1')
