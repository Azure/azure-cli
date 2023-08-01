# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import time
import unittest

from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, JMESPathCheck, live_only, StorageAccountPreparer)

TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))
from .common import TEST_LOCATION
from .utils import create_containerapp_env
from azext_containerapp.tests.latest.common import (
    write_test_file,
    clean_up_test_file,
    TEST_DIR, TEST_LOCATION)

class ContainerAppMountAzureFileTest(ScenarioTest):
    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(location=TEST_LOCATION)
    def test_container_app_mount_azurefile_e2e(self, resource_group):
        self.cmd('configure --defaults location={}'.format(TEST_LOCATION))

        env = self.create_random_name(prefix='env', length=24)
        app = self.create_random_name(prefix='app1', length=24)
        storage = self.create_random_name(prefix='storage', length=24)
        share = self.create_random_name(prefix='share', length=10)

        self.cmd(
            f'az storage account create --resource-group {resource_group}  --name {storage} --location {TEST_LOCATION} --kind StorageV2 --sku Standard_LRS --enable-large-file-share --output none')
        self.cmd(
            f'az storage share-rm create --resource-group {resource_group}  --storage-account {storage} --name {share} --quota 1024 --enabled-protocols SMB --output none')

        create_containerapp_env(self, env, resource_group, TEST_LOCATION)
        account_key = self.cmd(f'az storage account keys list -g {resource_group} -n {storage} --query "[0].value" '
                               '-otsv').output.strip()

        self.cmd(f'az containerapp env storage set -g {resource_group} -n {env} -a {storage} -k {account_key} -f {share} --storage-name {share} --access-mode ReadWrite')

        containerapp_env = self.cmd('containerapp env show -n {} -g {}'.format(env, resource_group), checks=[
            JMESPathCheck('name', env)

        ]).get_output_in_json()
        containerapp_yaml_text = f"""
                    location: {TEST_LOCATION}
                    type: Microsoft.App/containerApps
                    name: {app}
                    resourceGroup: {resource_group}
                    properties:
                        managedEnvironmentId: {containerapp_env["id"]}
                        configuration:
                            activeRevisionsMode: Single
                            ingress:
                                external: true
                                allowInsecure: true
                                targetPort: 80
                                traffic:
                                    - latestRevision: true
                                      weight: 100
                                transport: Auto
                        template:
                            containers:
                                - image: mcr.microsoft.com/k8se/quickstart:latest
                                  name: acamounttest
                                  resources:
                                      cpu: 0.5
                                      ephemeralStorage: 1Gi
                                      memory: 1Gi
                                  volumeMounts:
                                      - mountPath: /mnt/data
                                        volumeName: azure-files-volume
                                        subPath: sub
                            volumes:
                                - name: azure-files-volume
                                  storageType: AzureFile
                                  storageName: {share}
                                  mountOptions: uid=999,gid=999
                    """
        containerapp_file_name = f"{self._testMethodName}_containerapp.yml"

        write_test_file(containerapp_file_name, containerapp_yaml_text)
        self.cmd(
            f'az containerapp create -g {resource_group} --environment {env} -n {app} --yaml {containerapp_file_name}')

        self.cmd('containerapp show -g {} -n {}'.format(resource_group, app), checks=[
            JMESPathCheck('properties.template.volumes[0].storageType', 'AzureFile'),
            JMESPathCheck('properties.template.volumes[0].storageName', share),
            JMESPathCheck('properties.template.volumes[0].name', 'azure-files-volume'),
            JMESPathCheck('properties.template.volumes[0].mountOptions', 'uid=999,gid=999'),
            JMESPathCheck('properties.template.containers[0].volumeMounts[0].subPath', 'sub'),
            JMESPathCheck('properties.template.containers[0].volumeMounts[0].mountPath', '/mnt/data'),
            JMESPathCheck('properties.template.containers[0].volumeMounts[0].volumeName', 'azure-files-volume'),
        ])

        self.cmd('az containerapp revision list -g {} -n {}'.format(resource_group, app), checks=[
            JMESPathCheck('[0].properties.template.volumes[0].storageType', 'AzureFile'),
            JMESPathCheck('[0].properties.template.volumes[0].storageName', share),
            JMESPathCheck('[0].properties.template.volumes[0].name', 'azure-files-volume'),
            JMESPathCheck('[0].properties.template.volumes[0].mountOptions', 'uid=999,gid=999'),
            JMESPathCheck('[0].properties.template.containers[0].volumeMounts[0].subPath', 'sub'),
            JMESPathCheck('[0].properties.template.containers[0].volumeMounts[0].mountPath', '/mnt/data'),
            JMESPathCheck('[0].properties.template.containers[0].volumeMounts[0].volumeName', 'azure-files-volume'),
        ])

        containerapp_yaml_text = f"""
                           location: {TEST_LOCATION}
                           type: Microsoft.App/containerApps
                           name: {app}
                           resourceGroup: {resource_group}
                           properties:
                               managedEnvironmentId: {containerapp_env["id"]}
                               configuration:
                                   activeRevisionsMode: Single
                                   ingress:
                                       external: true
                                       allowInsecure: true
                                       targetPort: 80
                                       traffic:
                                           - latestRevision: true
                                             weight: 100
                                       transport: Auto
                               template:
                                   containers:
                                       - image: mcr.microsoft.com/k8se/quickstart:latest
                                         name: acamounttest
                                         resources:
                                             cpu: 0.5
                                             ephemeralStorage: 1Gi
                                             memory: 1Gi
                                         volumeMounts:
                                             - mountPath: /mnt/data
                                               volumeName: azure-files-volume
                                               subPath: sub2
                                   volumes:
                                       - name: azure-files-volume
                                         storageType: AzureFile
                                         storageName: {share}
                                         mountOptions: uid=1000,gid=1000
                           """
        containerapp_file_name = f"{self._testMethodName}_containerapp_1.yml"

        write_test_file(containerapp_file_name, containerapp_yaml_text)
        self.cmd(
            f'az containerapp update -g {resource_group} -n {app} --yaml {containerapp_file_name}')

        self.cmd('containerapp show -g {} -n {}'.format(resource_group, app), checks=[
            JMESPathCheck('properties.template.volumes[0].storageType', 'AzureFile'),
            JMESPathCheck('properties.template.volumes[0].storageName', share),
            JMESPathCheck('properties.template.volumes[0].name', 'azure-files-volume'),
            JMESPathCheck('properties.template.volumes[0].mountOptions', 'uid=1000,gid=1000'),
            JMESPathCheck('properties.template.containers[0].volumeMounts[0].subPath', 'sub2'),
            JMESPathCheck('properties.template.containers[0].volumeMounts[0].mountPath', '/mnt/data'),
            JMESPathCheck('properties.template.containers[0].volumeMounts[0].volumeName', 'azure-files-volume'),
        ])

        self.cmd('az containerapp revision list -g {} -n {}'.format(resource_group, app), checks=[
            JMESPathCheck('[1].properties.template.volumes[0].storageType', 'AzureFile'),
            JMESPathCheck('[1].properties.template.volumes[0].storageName', share),
            JMESPathCheck('[1].properties.template.volumes[0].name', 'azure-files-volume'),
            JMESPathCheck('[1].properties.template.volumes[0].mountOptions', 'uid=1000,gid=1000'),
            JMESPathCheck('[1].properties.template.containers[0].volumeMounts[0].subPath', 'sub2'),
            JMESPathCheck('[1].properties.template.containers[0].volumeMounts[0].mountPath', '/mnt/data'),
            JMESPathCheck('[1].properties.template.containers[0].volumeMounts[0].volumeName', 'azure-files-volume'),
        ])