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


class SBQueueScenarioTest(ScenarioTest):
    from azure.cli.testsdk.scenario_tests import AllowLargeResponse

    @AllowLargeResponse()
    @ResourceGroupPreparer(name_prefix='cli_test_sb_queue')
    def test_sb_queue(self, resource_group):
        self.kwargs.update({
            'namespacename': self.create_random_name(prefix='sb-nscli', length=20),
            'tags': {'tag1=value1', 'tag2=value2'},
            'sku': 'Standard',
            'tier': 'Standard',
            'authoname': self.create_random_name(prefix='cliAutho', length=20),
            'defaultauthorizationrule': 'RootManageSharedAccessKey',
            'accessrights': 'Listen',
            'accessrights1': 'Send',
            'primary': 'PrimaryKey',
            'secondary': 'SecondaryKey',
            'queuename': self.create_random_name(prefix='sb-queuecli', length=25),
            'queueauthoname': self.create_random_name(prefix='cliQueueAutho', length=25),
            'lockduration': 'PT10M',
            'lockduration1': 'PT11M'

        })

        # Create Namespace
        self.cmd(
            'servicebus namespace create --resource-group {rg} --name {namespacename} --tags {tags} --sku {sku}',
            checks=[self.check('sku.name', '{sku}')])

        # Get Created Namespace
        self.cmd('servicebus namespace show --resource-group {rg} --name {namespacename}',
                 checks=[self.check('sku.name', '{sku}')])

        # Create Queue
        self.cmd(
            'servicebus queue create --resource-group {rg} --namespace-name {namespacename} --name {queuename} --auto-delete-on-idle {lockduration} --max-size 1024 ',
            checks=[self.check('name', '{queuename}')])

        # Get Queue
        self.cmd('servicebus queue show --resource-group {rg} --namespace-name {namespacename} --name {queuename}',
                 checks=[self.check('name', '{queuename}')])

        # Update Queue
        self.cmd(
            'servicebus queue update --resource-group {rg} --namespace-name {namespacename} --name {queuename} --auto-delete-on-idle {lockduration1} ',
            checks=[self.check('name', '{queuename}')])

        # Queue List
        self.cmd('servicebus queue list --resource-group {rg} --namespace-name {namespacename}')

        # Create Authoriazation Rule
        self.cmd(
            'servicebus queue authorization-rule create --resource-group {rg} --namespace-name {namespacename} --queue-name {queuename} --name {authoname} --rights {accessrights}',
            checks=[self.check('name', '{authoname}')])

        # Get Create Authorization Rule
        self.cmd(
            'servicebus queue authorization-rule show --resource-group {rg} --namespace-name {namespacename} --queue-name {queuename} --name {authoname}',
            checks=[self.check('name', '{authoname}')])

        # Update Authoriazation Rule
        self.cmd(
            'servicebus queue authorization-rule update --resource-group {rg} --namespace-name {namespacename} --queue-name {queuename} --name {authoname} --rights {accessrights1}',
            checks=[self.check('name', '{authoname}')])

        # Get Authorization Rule Listkeys
        self.cmd(
            'servicebus queue authorization-rule keys list --resource-group {rg} --namespace-name {namespacename} --queue-name {queuename} --name {authoname}')

        # Regeneratekeys - Primary
        regenrateprimarykeyresult = self.cmd(
            'servicebus queue authorization-rule keys renew --resource-group {rg} --namespace-name {namespacename} --queue-name {queuename} --name {authoname} --key {primary}')
        self.assertIsNotNone(regenrateprimarykeyresult)

        # Regeneratekeys - Secondary
        regenratesecondarykeyresult = self.cmd(
            'servicebus queue authorization-rule keys renew --resource-group {rg} --namespace-name {namespacename} --queue-name {queuename} --name {authoname} --key {secondary}')
        self.assertIsNotNone(regenratesecondarykeyresult)

        # Delete Queue Authorization Rule
        self.cmd(
            'servicebus queue authorization-rule delete --resource-group {rg} --namespace-name {namespacename} --queue-name {queuename} --name {authoname}')

        # Delete Queue
        self.cmd('servicebus queue delete --resource-group {rg} --namespace-name {namespacename} --name {queuename}')

        # Delete Namespace
        self.cmd('servicebus namespace delete --resource-group {rg} --name {namespacename}')
