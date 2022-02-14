# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# AZURE CLI SERVICEBUS - CRUD TEST DEFINITIONS

import time
from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, live_only)
from knack.util import CLIError


# pylint: disable=line-too-long
# pylint: disable=too-many-lines


class SBNSMigrationCRUDScenarioTest(ScenarioTest):
    from azure.cli.testsdk.scenario_tests import AllowLargeResponse

    # Test playback fails and the live-only flag will be removed once it is addressed
    @live_only()
    @AllowLargeResponse()
    @ResourceGroupPreparer(name_prefix='cli_test_sb_migration')
    def test_sb_migration(self, resource_group):
        from azure.mgmt.servicebus.models import ProvisioningStateDR
        self.kwargs.update({
            'loc_south': 'SouthCentralUS',
            'loc_north': 'NorthCentralUS',
            'namespacenamestandard': self.create_random_name(prefix='sb-std-nscli', length=20),
            'namespacenamepremium': self.create_random_name(prefix='sb-pre-nscli', length=20),
            'tags': {'tag1: value1', 'tag2: value2'},
            'sku': 'Premium',
            'sku_std': 'Standard',
            'authoname': self.create_random_name(prefix='cliAutho', length=20),
            'defaultauthorizationrule': 'RootManageSharedAccessKey',
            'accessrights': 'Send',
            'primary': 'PrimaryKey',
            'secondary': 'SecondaryKey',
            'postmigrationname': self.create_random_name(prefix='clipostmigration', length=20),
            'alternatename': self.create_random_name(prefix='cliAlter', length=20),
            'id': '',
            'test': '',
            'queuename': '',
            'topicname': '',
            'partnernamespaceid': ''
        })

        self.cmd('servicebus namespace exists --name {namespacenamestandard}',
                 checks=[self.check('nameAvailable', True)])

        # Create Namespace - Standard
        self.cmd(
            'servicebus namespace create --resource-group {rg} --name {namespacenamestandard} --location {loc_south} --tags {tags} --sku {sku_std}',
            checks=[self.check('sku.name', '{sku_std}')])

        # Get Created Namespace - Standard
        self.cmd('servicebus namespace show --resource-group {rg} --name {namespacenamestandard}',
                 checks=[self.check('sku.name', '{sku_std}')])

        # Create Namespace - Primary
        self.cmd(
            'servicebus namespace create --resource-group {rg} --name {namespacenamepremium} --location {loc_north} --tags {tags} --sku {sku}',
            checks=[self.check('sku.name', '{sku}')])

        # Get Created Namespace - Primary
        getnamespace2result = self.cmd(
            'servicebus namespace show --resource-group {rg} --name {namespacenamepremium}',
            checks=[self.check('sku.name', '{sku}')]).get_output_in_json()

        # Create Authoriazation Rule
        self.cmd(
            'servicebus namespace authorization-rule create --resource-group {rg} --namespace-name {namespacenamestandard} --name {authoname} --rights {accessrights}',
            checks=[self.check('name', '{authoname}')])

        partnernamespaceid = getnamespace2result['id']
        self.kwargs.update({'id': partnernamespaceid})

        # Get Create Authorization Rule
        self.cmd(
            'servicebus namespace authorization-rule show --resource-group {rg} --namespace-name {namespacenamestandard} --name {authoname}',
            checks=[self.check('name', '{authoname}')])

        # Create Queues under Standrad namespace
        for x in range(0, 10):
            queuenamestr = 'queue' + repr(x)
            self.kwargs.update({'queuename': queuenamestr})
            self.cmd(
                'servicebus queue create --resource-group {rg} --namespace-name {namespacenamestandard} --name {queuename}',
                checks=[self.check('name', '{queuename}')])

        # Create Topics under Standrad namespace
        for x in range(0, 10):
            topicnamestr = 'topic' + repr(x)
            self.kwargs.update({'topicname': topicnamestr})
            self.cmd(
                'servicebus topic create --resource-group {rg} --namespace-name {namespacenamestandard} --name {topicname}',
                checks=[self.check('name', '{topicname}')])

        time.sleep(10)

        # Create Migration
        self.cmd(
            'servicebus migration start  --resource-group {rg} --name {namespacenamestandard} --target-namespace {id} --post-migration-name {postmigrationname}')

        # get Migration
        getmigration = self.cmd(
            'servicebus migration show  --resource-group {rg} --name {namespacenamestandard}').get_output_in_json()

        # Complete Migration
        self.cmd(
            'servicebus migration complete  --resource-group {rg} --name {namespacenamestandard}')

        # get Migration
        getmigration = self.cmd(
            'servicebus migration show  --resource-group {rg} --name {namespacenamestandard}').get_output_in_json()

        # check for the migration provisioning succeeded
        while getmigration['provisioningState'] != ProvisioningStateDR.succeeded.value:
            time.sleep(30)
            getmigration = self.cmd(
                'servicebus migration show  --resource-group {rg} --name {namespacenamestandard}').get_output_in_json()

        # check for the migration PendingReplicationOperationsCount is 0 or null
        while getmigration['migrationState'] != 'Active':
            time.sleep(30)
            getmigration = self.cmd(
                'servicebus migration show  --resource-group {rg} --name {namespacenamestandard}').get_output_in_json()

        # Get Authorization Rule - Premium
        self.cmd(
            'servicebus namespace authorization-rule show --resource-group {rg} --namespace-name {namespacenamepremium} --name {authoname}',
            checks=[self.check('name', '{authoname}')])

        # Get all queues from Premium namespace
        listqueues1 = self.cmd(
            'servicebus queue list --resource-group {rg} --namespace-name {namespacenamepremium}').get_output_in_json()
        self.assertIsNotNone(listqueues1)
        self.assertGreaterEqual(len(listqueues1), 10, 'Premium - get all queues count not 10')

        # Get all queues from Premium namespace
        listtopics = self.cmd(
            'servicebus topic list --resource-group {rg} --namespace-name {namespacenamepremium}').get_output_in_json()
        self.assertIsNotNone(listtopics)
        self.assertGreaterEqual(len(listtopics), 10, 'Premium - get all topics count not 10')

        time.sleep(30)

        # get namespace
        getnamespace = self.cmd(
            'servicebus namespace show  --resource-group {rg} --name {namespacenamestandard}').get_output_in_json()

        # check for the namespace provisioning succeeded
        while getnamespace['provisioningState'] != ProvisioningStateDR.succeeded.value:
            time.sleep(30)
            getnamespace = self.cmd(
                'servicebus namespace show  --resource-group {rg} --name {namespacenamestandard}').get_output_in_json()

        # Delete Namespace - Standard
        self.cmd('servicebus namespace delete --resource-group {rg} --name {namespacenamestandard}')

        # get namespace
        getnamespace = self.cmd(
            'servicebus namespace show  --resource-group {rg} --name {namespacenamepremium}').get_output_in_json()

        # check for the namespace provisioning succeeded
        while getnamespace['provisioningState'] != ProvisioningStateDR.succeeded.value:
            time.sleep(30)
            getnamespace = self.cmd(
                'servicebus namespace show  --resource-group {rg} --name {namespacenamepremium}').get_output_in_json()
