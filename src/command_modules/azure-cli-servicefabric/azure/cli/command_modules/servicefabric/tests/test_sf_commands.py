# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import unittest
import os

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer
from azure.cli.testsdk import JMESPathCheck as JMESPathCheckV2
from azure.cli.testsdk.vcr_test_base import (ResourceGroupVCRTestBase,
                                             JMESPathCheck, NoneCheck)


class ServiceFabricNewClusterTest(ResourceGroupVCRTestBase):
    def __init__(self, test_method):
        super(ServiceFabricNewClusterTest, self).__init__(
            __file__, test_method)

    def test_create(self):
        self.execute()

    def body(self):
        rg = 'sfcli7'
        name = 'sfcli7'
        location = 'westus'

        self.cmd('sf cluster create --resource-group {} --location {} --cluster-size 1 --secret-identifier https://sfcli4.vault.azure.net/secrets/sfcli4201708250843/2b9981be18164360a21e6face7b67a77 --vm-password User@123456789'.format(rg, location),
                 checks=[JMESPathCheck('cluster.name', name)])


class ServiceFabricClientCertTest(ResourceGroupVCRTestBase):
    def __init__(self, test_method):
        super(ServiceFabricClientCertTest, self).__init__(
            __file__, test_method)

    def test_client_cert(self):
        self.execute()

    def body(self):
        rg = 'sfcli1'
        name = 'sfcli1'

        self.cmd('sf cluster list --resource-group {}'.format(rg),
                 checks=[JMESPathCheck('type(@)', 'array')])

        self.cmd('sf cluster show --resource-group {} --name {}'.format(rg, name),
                 checks=[JMESPathCheck('name', name)])

        self.cmd('sf cluster upgrade-type set --resource-group {} --cluster-name {} --upgrade-mode automatic'.
                 format(rg, name),
                 checks=[JMESPathCheck('upgradeMode', 'Automatic')])

        test_thumbprint = '9B609A389BD4597BEEFABFB363BF2BBF2E806001'
        self.cmd('sf cluster client-certificate add --resource-group {} --name {}  --thumbprint {}'.format(rg, name, test_thumbprint),
                 checks=[JMESPathCheck('clientCertificateThumbprints[0].certificateThumbprint', test_thumbprint),
                         JMESPathCheck('clientCertificateThumbprints[0].isAdmin', False)])

        self.cmd('sf cluster client-certificate remove --resource-group {} --name {} --thumbprints {}'.format(rg, name, test_thumbprint),
                 checks=[JMESPathCheck('length(clientCertificateThumbprints)', 0)])


class ServiceFabricRemoveNodeTest(ResourceGroupVCRTestBase):
    def __init__(self, test_method):
        super(ServiceFabricRemoveNodeTest, self).__init__(
            __file__, test_method)

    def test_remove_node(self):
        self.execute()

    def body(self):
        rg = 'sfcli6'
        name = 'sfcli6'

        self.cmd('sf cluster node remove -g {} -n {} --node-type nt1vm  --number-of-nodes-to-remove 1'.format(rg, name),
                 checks=[JMESPathCheck('nodeTypes[0].vmInstanceCount', 5)])


class ServiceFabricReliabilityTest(ResourceGroupVCRTestBase):
    def __init__(self, test_method):
        super(ServiceFabricReliabilityTest, self).__init__(
            __file__, test_method)

    def test_reliability(self):
        self.execute()

    def body(self):
        rg = 'sfcli6'
        name = 'sfcli6'

        reliability_level = 'Silver'
        self.cmd('sf cluster reliability update --resource-group {} --name {} --reliability-level {}'.format(rg, name, reliability_level),
                 checks=[JMESPathCheck('reliabilityLevel', reliability_level)])


class ServiceFabricDurabilityTest(ResourceGroupVCRTestBase):
    def __init__(self, test_method):
        super(ServiceFabricDurabilityTest, self).__init__(
            __file__, test_method)

    def test_durability(self):
        self.execute()

    def body(self):
        rg = 'appcanary-rg'
        name = 'appcanary'

        durability_level = 'Bronze'
        self.cmd('sf cluster durability update --resource-group {} --name {} --durability-level {} --node-type FE'.format(rg, name, durability_level),
                 checks=[JMESPathCheck('nodeTypes[0].durabilityLevel', durability_level)])


class ServiceFabricNodeTest(ResourceGroupVCRTestBase):
    def __init__(self, test_method):
        super(ServiceFabricNodeTest, self).__init__(
            __file__, test_method)

    def test_node(self):
        self.execute()

    def body(self):
        rg = 'sfcli7'
        name = 'sfcli7'

        self.cmd('sf cluster node add -g {} -n {} --node-type nt1vm  --number-of-nodes-to-add 1'.format(rg, name),
                 checks=[JMESPathCheck('nodeTypes[0].vmInstanceCount', 2)])


class ServiceFabricSettingTest(ResourceGroupVCRTestBase):
    def __init__(self, test_method):
        super(ServiceFabricSettingTest, self).__init__(
            __file__, test_method)

    def test_setting(self):
        self.execute()

    def body(self):
        rg = 'sfcli2'
        name = 'sfcli2'

        self.cmd('sf cluster setting set --resource-group {} --name {} --section NamingService --parameter MaxOperationTimeout --value 10001'.
                 format(rg, name),
                 checks=[JMESPathCheck('fabricSettings[1].name', 'NamingService'),
                         JMESPathCheck(
                             'fabricSettings[1].parameters[0].name', 'MaxOperationTimeout'),
                         JMESPathCheck('fabricSettings[1].parameters[0].value', '10001')])

        self.cmd('sf cluster setting remove --resource-group {} --name {} --section NamingService --parameter MaxOperationTimeout'.format(rg, name),
                 checks=[JMESPathCheck('length(fabricSettings)', 1)])


class ServiceFabricClusterCertTest(ResourceGroupVCRTestBase):
    def __init__(self, test_method):
        super(ServiceFabricClusterCertTest, self).__init__(
            __file__, test_method)

    def test_cluster_cert(self):
        self.execute()

    def body(self):
        rg = 'sfcli4'
        name = 'sfcli4'

        cluster = self.cmd(
            'sf cluster certificate add --resource-group {} --cluster-name {} --secret-identifier https://sfcli4.vault.azure.net/secrets/sfcli4201708250843/2b9981be18164360a21e6face7b67a77'.format(rg, name))
        assert cluster['certificate']['thumbprintSecondary']

        cluster = self.cmd('sf cluster certificate remove --resource-group {} --cluster-name {} --thumbprint {}'.format(
            rg, name, cluster['certificate']['thumbprintSecondary']))
        assert not cluster['certificate']['thumbprintSecondary']


if __name__ == '__main__':
    unittest.main()
