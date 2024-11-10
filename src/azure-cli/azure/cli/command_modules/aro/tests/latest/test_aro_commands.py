# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import unittest
from random import randint
from unittest import mock


from knack.log import get_logger
from azure.cli.command_modules.aro.tests.latest.custom_preparers import AROClusterServicePrincipalPreparer
from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer
from azure.cli.testsdk.checkers import StringContainCheck
from azure.cli.testsdk.scenario_tests import AllowLargeResponse

logger = get_logger(__name__)


class AroScenarioTests(ScenarioTest):

    @AllowLargeResponse()
    @ResourceGroupPreparer(random_name_length=28, name_prefix='cli_test_aro', location='eastus')
    @AROClusterServicePrincipalPreparer(name_prefix='cli_test_aro')
    def test_aro_public_cluster(self, resource_group):
        from azure.mgmt.core.tools import resource_id

        subscription = self.get_subscription_id()

        master_subnet = self.create_random_name('dev_master', 14)
        worker_subnet = self.create_random_name('dev_worker', 14)
        name = self.create_random_name('aro', 14)

        temp_kubeconfig_path = self.create_random_name('kubeconfig', 24) + '.tmp'

        self.kwargs.update({
            'name': name,
            'resource_group': resource_group,
            'subscription': subscription,
            'master_subnet': master_subnet,
            'worker_subnet': worker_subnet,
            'master_ip_range': '10.{}.{}.0/24'.format(randint(0, 127), randint(0, 255)),
            'worker_ip_range': '10.{}.{}.0/24'.format(randint(0, 127), randint(0, 255)),
            'master_subnet_resource': resource_id(subscription=subscription, resource_group=resource_group,
                                                  namespace='Microsoft.Network', type='virtualNetworks',
                                                  child_type_1='subnets', name='dev-vnet', child_name_1=master_subnet),
            'worker_subnet_resource': resource_id(subscription=subscription, resource_group=resource_group,
                                                  namespace='Microsoft.Network', type='virtualNetworks',
                                                  child_type_1='subnets', name='dev-vnet', child_name_1=worker_subnet),
            'temp_kubeconfig_path': temp_kubeconfig_path,
        })

        self.cmd('network vnet create -g {rg} -n dev-vnet --address-prefixes 10.0.0.0/9')
        self.cmd(
            'network vnet subnet create -g {rg} --vnet-name dev-vnet -n {master_subnet} --address-prefixes {master_ip_range} --service-endpoints Microsoft.ContainerRegistry --default-outbound false')
        self.cmd(
            'network vnet subnet create -g {rg} --vnet-name dev-vnet -n {worker_subnet} --address-prefixes {worker_ip_range} --service-endpoints Microsoft.ContainerRegistry --default-outbound false')
        self.cmd(
            'network vnet subnet update -g {rg} --vnet-name dev-vnet -n {master_subnet} --private-link-service-network-policies Disabled')

        # aro validate
        with mock.patch('azure.cli.command_modules.aro._rbac._gen_uuid', side_effect=self.create_guid):
            self.cmd(
                'aro validate -g {rg} -n {name} --client-id {aro_csp} --client-secret {aro_csp_pass} --master-subnet {master_subnet_resource} --worker-subnet {worker_subnet_resource} --subscription {subscription}')

        # aro create
        with mock.patch('azure.cli.command_modules.aro._rbac._gen_uuid', side_effect=self.create_guid):
            self.cmd(
                'aro create -g {rg} -n {name} --client-id {aro_csp} --client-secret {aro_csp_pass} --master-subnet {master_subnet_resource} --worker-subnet {worker_subnet_resource} --subscription {subscription} --tags test=create',
                checks=[
                    self.check('tags.test', 'create'),
                    self.check('name', '{name}'),
                    self.check('masterProfile.subnetId', '{master_subnet_resource}'),
                    self.check('workerProfiles[0].subnetId', '{worker_subnet_resource}'),
                    self.check('provisioningState', 'Succeeded')
                ])

        # aro list-credentials
        self.cmd('aro list-credentials -g {rg} -n {name} --subscription {subscription}',
                 checks=[self.check('kubeadminUsername', 'kubeadmin')])

        # aro get-admin-kubeconfig
        try:
            self.cmd(
                'aro get-admin-kubeconfig -g {rg} -n {name} --subscription {subscription} -f {temp_kubeconfig_path}')
            self.assertGreater(os.path.getsize(temp_kubeconfig_path), 0)
        finally:
            os.remove(temp_kubeconfig_path)

        # aro show
        self.cmd('aro show -g {rg} -n {name} --subscription {subscription} --output table', checks=[
            StringContainCheck(name),
            StringContainCheck(resource_group),
            StringContainCheck('eastus'),
            StringContainCheck('Succeeded'),
        ])

        # aro list
        self.cmd('aro list -g {rg} --subscription {subscription}', checks=[
            self.check('[0].name', '{name}'),
            self.check('[0].provisioningState', 'Succeeded'),
            self.check_pattern('[0].id', '.*{name}')
        ])

        # aro update
        self.cmd('aro update -g {rg} -n {name} --subscription {subscription}', expect_failure=False)

        # aro delete
        self.cmd('aro delete -y -g {rg} -n {name} --subscription {subscription}', expect_failure=False)
