# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import unittest
from random import randint
from unittest import mock


from knack.log import get_logger
from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer
from azure.cli.testsdk.checkers import StringContainCheck
from azure.cli.testsdk.scenario_tests import AllowLargeResponse

logger = get_logger(__name__)


class AroScenarioTests(ScenarioTest):

    @AllowLargeResponse()
    @ResourceGroupPreparer(random_name_length=28, name_prefix='cli_test_aro_create', location='eastus')
    def test_aro_create(self, resource_group):
        from msrestazure.tools import resource_id

        subscription = self.get_subscription_id()

        master_subnet = self.create_random_name('dev_master', 14)
        worker_subnet = self.create_random_name('dev_worker', 14)

        self.kwargs.update({
            'name': self.create_random_name('aro', 14),
            'resource_group': resource_group,
            'subscription': subscription,
            'master_subnet': master_subnet,
            'worker_subnet': worker_subnet,
            'master_ip_range': '10.{}.{}.0/24'.format(randint(0, 127), randint(0, 255)),
            'worker_ip_range': '10.{}.{}.0/24'.format(randint(0, 127), randint(0, 255)),
            'master_subnet_resource': resource_id(subscription=subscription, resource_group=resource_group, namespace='Microsoft.Network', type='virtualNetworks', child_type_1='subnets', name='dev-vnet', child_name_1=master_subnet),
            'worker_subnet_resource': resource_id(subscription=subscription, resource_group=resource_group, namespace='Microsoft.Network', type='virtualNetworks', child_type_1='subnets', name='dev-vnet', child_name_1=worker_subnet),
        })

        self.cmd('network vnet create -g {rg} -n dev-vnet --address-prefixes 10.0.0.0/9')
        self.cmd('network vnet subnet create -g {rg} --vnet-name dev-vnet -n {master_subnet} --address-prefixes {master_ip_range} --service-endpoints Microsoft.ContainerRegistry')
        self.cmd('network vnet subnet create -g {rg} --vnet-name dev-vnet -n {worker_subnet} --address-prefixes {worker_ip_range} --service-endpoints Microsoft.ContainerRegistry')
        self.cmd('network vnet subnet update -g {rg} --vnet-name dev-vnet -n {master_subnet} --disable-private-link-service-network-policies true')

        with mock.patch('azure.cli.command_modules.aro._rbac._gen_uuid', side_effect=self.create_guid):
            self.cmd('aro create -g {rg} -n {name} --master-subnet {master_subnet_resource} --worker-subnet {worker_subnet_resource} --subscription {subscription} --tags test=create', checks=[
                self.check('tags.test', 'create'),
                self.check('name', '{name}'),
                self.check('masterProfile.subnetId', '{master_subnet_resource}'),
                self.check('workerProfiles[0].subnetId', '{worker_subnet_resource}'),
                self.check('provisioningState', 'Succeeded')
            ])

    @AllowLargeResponse()
    @ResourceGroupPreparer(random_name_length=28, name_prefix='cli_test_aro_list_cred', location='eastus')
    def test_aro_list_credentials(self, resource_group):
        from msrestazure.tools import resource_id

        subscription = self.get_subscription_id()

        master_subnet = self.create_random_name('dev_master', 14)
        worker_subnet = self.create_random_name('dev_worker', 14)

        self.kwargs.update({
            'name': self.create_random_name('aro', 14),
            'resource_group': resource_group,
            'subscription': subscription,
            'master_subnet': master_subnet,
            'worker_subnet': worker_subnet,
            'master_ip_range': '10.{}.{}.0/24'.format(randint(0, 127), randint(0, 255)),
            'worker_ip_range': '10.{}.{}.0/24'.format(randint(0, 127), randint(0, 255)),
            'master_subnet_resource': resource_id(subscription=subscription, resource_group=resource_group, namespace='Microsoft.Network', type='virtualNetworks', child_type_1='subnets', name='dev-vnet', child_name_1=master_subnet),
            'worker_subnet_resource': resource_id(subscription=subscription, resource_group=resource_group, namespace='Microsoft.Network', type='virtualNetworks', child_type_1='subnets', name='dev-vnet', child_name_1=worker_subnet),
        })

        self.cmd('network vnet create -g {rg} -n dev-vnet --address-prefixes 10.0.0.0/9')
        self.cmd('network vnet subnet create -g {rg} --vnet-name dev-vnet -n {master_subnet} --address-prefixes {master_ip_range} --service-endpoints Microsoft.ContainerRegistry')
        self.cmd('network vnet subnet create -g {rg} --vnet-name dev-vnet -n {worker_subnet} --address-prefixes {worker_ip_range} --service-endpoints Microsoft.ContainerRegistry')
        self.cmd('network vnet subnet update -g {rg} --vnet-name dev-vnet -n {master_subnet} --disable-private-link-service-network-policies true')

        with mock.patch('azure.cli.command_modules.aro._rbac._gen_uuid', side_effect=self.create_guid):
            self.cmd('aro create -g {rg} -n {name} --master-subnet {master_subnet_resource} --worker-subnet {worker_subnet_resource} --subscription {subscription} --tags test=list-cred')

        self.cmd('aro list-credentials -g {rg} -n {name} --subscription {subscription}', checks=[self.check('kubeadminUsername', 'kubeadmin')])

    @AllowLargeResponse()
    @ResourceGroupPreparer(random_name_length=28, name_prefix='cli_test_aro_show', location='eastus')
    def test_aro_show(self, resource_group):
        from msrestazure.tools import resource_id

        subscription = self.get_subscription_id()

        master_subnet = self.create_random_name('dev_master', 14)
        worker_subnet = self.create_random_name('dev_worker', 14)

        name = self.create_random_name('aro', 14)
        self.kwargs.update({
            'name': name,
            'resource_group': resource_group,
            'subscription': subscription,
            'master_subnet': master_subnet,
            'worker_subnet': worker_subnet,
            'master_ip_range': '10.{}.{}.0/24'.format(randint(0, 127), randint(0, 255)),
            'worker_ip_range': '10.{}.{}.0/24'.format(randint(0, 127), randint(0, 255)),
            'master_subnet_resource': resource_id(subscription=subscription, resource_group=resource_group, namespace='Microsoft.Network', type='virtualNetworks', child_type_1='subnets', name='dev-vnet', child_name_1=master_subnet),
            'worker_subnet_resource': resource_id(subscription=subscription, resource_group=resource_group, namespace='Microsoft.Network', type='virtualNetworks', child_type_1='subnets', name='dev-vnet', child_name_1=worker_subnet),
        })

        self.cmd('network vnet create -g {rg} -n dev-vnet --address-prefixes 10.0.0.0/9')
        self.cmd('network vnet subnet create -g {rg} --vnet-name dev-vnet -n {master_subnet} --address-prefixes {master_ip_range} --service-endpoints Microsoft.ContainerRegistry')
        self.cmd('network vnet subnet create -g {rg} --vnet-name dev-vnet -n {worker_subnet} --address-prefixes {worker_ip_range} --service-endpoints Microsoft.ContainerRegistry')
        self.cmd('network vnet subnet update -g {rg} --vnet-name dev-vnet -n {master_subnet} --disable-private-link-service-network-policies true')

        with mock.patch('azure.cli.command_modules.aro._rbac._gen_uuid', side_effect=self.create_guid):
            self.cmd('aro create -g {rg} -n {name} --master-subnet {master_subnet_resource} --worker-subnet {worker_subnet_resource} --subscription {subscription} --tags test=show')

        self.cmd('aro show -g {rg} -n {name} --subscription {subscription} --output table', checks=[
            StringContainCheck(name),
            StringContainCheck(resource_group),
            StringContainCheck('eastus'),
            StringContainCheck('Succeeded'),
        ])

    @AllowLargeResponse()
    @ResourceGroupPreparer(random_name_length=28, name_prefix='cli_test_aro_list', location='eastus')
    def test_aro_list(self, resource_group):
        from msrestazure.tools import resource_id

        subscription = self.get_subscription_id()

        master_subnet = self.create_random_name('dev_master', 14)
        worker_subnet = self.create_random_name('dev_worker', 14)

        self.kwargs.update({
            'name': self.create_random_name('aro', 14),
            'resource_group': resource_group,
            'subscription': subscription,
            'master_subnet': master_subnet,
            'worker_subnet': worker_subnet,
            'master_ip_range': '10.{}.{}.0/24'.format(randint(0, 127), randint(0, 255)),
            'worker_ip_range': '10.{}.{}.0/24'.format(randint(0, 127), randint(0, 255)),
            'master_subnet_resource': resource_id(subscription=subscription, resource_group=resource_group, namespace='Microsoft.Network', type='virtualNetworks', child_type_1='subnets', name='dev-vnet', child_name_1=master_subnet),
            'worker_subnet_resource': resource_id(subscription=subscription, resource_group=resource_group, namespace='Microsoft.Network', type='virtualNetworks', child_type_1='subnets', name='dev-vnet', child_name_1=worker_subnet),
        })

        self.cmd('network vnet create -g {rg} -n dev-vnet --address-prefixes 10.0.0.0/9')
        self.cmd('network vnet subnet create -g {rg} --vnet-name dev-vnet -n {master_subnet} --address-prefixes {master_ip_range} --service-endpoints Microsoft.ContainerRegistry')
        self.cmd('network vnet subnet create -g {rg} --vnet-name dev-vnet -n {worker_subnet} --address-prefixes {worker_ip_range} --service-endpoints Microsoft.ContainerRegistry')
        self.cmd('network vnet subnet update -g {rg} --vnet-name dev-vnet -n {master_subnet} --disable-private-link-service-network-policies true')

        with mock.patch('azure.cli.command_modules.aro._rbac._gen_uuid', side_effect=self.create_guid):
            self.cmd('aro create -g {rg} -n {name} --master-subnet {master_subnet_resource} --worker-subnet {worker_subnet_resource} --subscription {subscription} --tags test=list')

        self.cmd('aro list -g {rg} --subscription {subscription}', checks=[
            self.check('[0].name', '{name}'),
            self.check('[0].provisioningState', 'Succeeded'),
            self.check_pattern('[0].id', '.*{name}')
        ])

    @AllowLargeResponse()
    @ResourceGroupPreparer(random_name_length=28, name_prefix='cli_test_aro_delete', location='eastus')
    def test_aro_delete(self, resource_group):
        from msrestazure.tools import resource_id

        subscription = self.get_subscription_id()

        master_subnet = self.create_random_name('dev_master', 14)
        worker_subnet = self.create_random_name('dev_worker', 14)

        self.kwargs.update({
            'name': self.create_random_name('aro', 14),
            'resource_group': resource_group,
            'subscription': subscription,
            'master_subnet': master_subnet,
            'worker_subnet': worker_subnet,
            'master_ip_range': '10.{}.{}.0/24'.format(randint(0, 127), randint(0, 255)),
            'worker_ip_range': '10.{}.{}.0/24'.format(randint(0, 127), randint(0, 255)),
            'master_subnet_resource': resource_id(subscription=subscription, resource_group=resource_group, namespace='Microsoft.Network', type='virtualNetworks', child_type_1='subnets', name='dev-vnet', child_name_1=master_subnet),
            'worker_subnet_resource': resource_id(subscription=subscription, resource_group=resource_group, namespace='Microsoft.Network', type='virtualNetworks', child_type_1='subnets', name='dev-vnet', child_name_1=worker_subnet),
        })

        self.cmd('network vnet create -g {rg} -n dev-vnet --address-prefixes 10.0.0.0/9')
        self.cmd('network vnet subnet create -g {rg} --vnet-name dev-vnet -n {master_subnet} --address-prefixes {master_ip_range} --service-endpoints Microsoft.ContainerRegistry')
        self.cmd('network vnet subnet create -g {rg} --vnet-name dev-vnet -n {worker_subnet} --address-prefixes {worker_ip_range} --service-endpoints Microsoft.ContainerRegistry')
        self.cmd('network vnet subnet update -g {rg} --vnet-name dev-vnet -n {master_subnet} --disable-private-link-service-network-policies true')

        with mock.patch('azure.cli.command_modules.aro._rbac._gen_uuid', side_effect=self.create_guid):
            self.cmd('aro create -g {rg} -n {name} --master-subnet {master_subnet_resource} --worker-subnet {worker_subnet_resource} --subscription {subscription} --tags test=delete')

        self.cmd('aro delete -y -g {rg} -n {name} --subscription {subscription}', expect_failure=False)

    @AllowLargeResponse()
    @ResourceGroupPreparer(random_name_length=28, name_prefix='cli_test_aro_update', location='eastus')
    def test_aro_update(self, resource_group):
        from msrestazure.tools import resource_id

        subscription = self.get_subscription_id()

        master_subnet = self.create_random_name('dev_master', 14)
        worker_subnet = self.create_random_name('dev_worker', 14)

        self.kwargs.update({
            'name': self.create_random_name('aro', 14),
            'resource_group': resource_group,
            'subscription': subscription,
            'master_subnet': master_subnet,
            'worker_subnet': worker_subnet,
            'master_ip_range': '10.{}.{}.0/24'.format(randint(0, 127), randint(0, 255)),
            'worker_ip_range': '10.{}.{}.0/24'.format(randint(0, 127), randint(0, 255)),
            'master_subnet_resource': resource_id(subscription=subscription, resource_group=resource_group, namespace='Microsoft.Network', type='virtualNetworks', child_type_1='subnets', name='dev-vnet', child_name_1=master_subnet),
            'worker_subnet_resource': resource_id(subscription=subscription, resource_group=resource_group, namespace='Microsoft.Network', type='virtualNetworks', child_type_1='subnets', name='dev-vnet', child_name_1=worker_subnet),
        })

        self.cmd('network vnet create -g {rg} -n dev-vnet --address-prefixes 10.0.0.0/9')
        self.cmd('network vnet subnet create -g {rg} --vnet-name dev-vnet -n {master_subnet} --address-prefixes {master_ip_range} --service-endpoints Microsoft.ContainerRegistry')
        self.cmd('network vnet subnet create -g {rg} --vnet-name dev-vnet -n {worker_subnet} --address-prefixes {worker_ip_range} --service-endpoints Microsoft.ContainerRegistry')
        self.cmd('network vnet subnet update -g {rg} --vnet-name dev-vnet -n {master_subnet} --disable-private-link-service-network-policies true')

        with mock.patch('azure.cli.command_modules.aro._rbac._gen_uuid', side_effect=self.create_guid):
            self.cmd('aro create -g {rg} -n {name} --master-subnet {master_subnet_resource} --worker-subnet {worker_subnet_resource} --subscription {subscription} --tags test=update')

        self.cmd('aro update -g {rg} -n {name} --subscription {subscription}', expect_failure=False)
