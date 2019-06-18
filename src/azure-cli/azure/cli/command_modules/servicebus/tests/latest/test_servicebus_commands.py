# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# AZURE CLI SERVICEBUS - CURD TEST DEFINITIONS

import time
from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, live_only)
from knack.util import CLIError


# pylint: disable=line-too-long
# pylint: disable=too-many-lines


class SBNamespaceCURDScenarioTest(ScenarioTest):
    from azure_devtools.scenario_tests import AllowLargeResponse

    @AllowLargeResponse()
    @ResourceGroupPreparer(name_prefix='cli_test_sb_namespace')
    def test_sb_namespace(self, resource_group):
        self.kwargs.update({
            'namespacename': self.create_random_name(prefix='sb-nscli', length=20),
            'tags': {'tag1=value1'},
            'tags2': {'tag2=value2'},
            'sku': 'Standard',
            'tier': 'Standard',
            'authoname': self.create_random_name(prefix='cliAutho', length=20),
            'defaultauthorizationrule': 'RootManageSharedAccessKey',
            'accessrights': 'Send',
            'accessrights1': 'Listen',
            'primary': 'PrimaryKey',
            'secondary': 'SecondaryKey'
        })

        # Check for the NameSpace name Availability
        self.cmd('servicebus namespace exists --name {namespacename}',
                 checks=[self.check('nameAvailable', True)])

        # Create Namespace
        self.cmd(
            'servicebus namespace create --resource-group {rg} --name {namespacename} --tags {tags} --sku {sku}',
            checks=[self.check('sku.name', '{sku}')])

        # Get Created Namespace
        self.cmd('servicebus namespace show --resource-group {rg} --name {namespacename}',
                 checks=[self.check('sku.name', '{sku}')])

        # Update Namespace
        self.cmd(
            'servicebus namespace update --resource-group {rg} --name {namespacename} --tags {tags}',
            checks=[self.check('sku.name', '{sku}')])

        # Get Created Namespace list by subscription
        listnamespaceresult = self.cmd('servicebus namespace list').output
        self.assertGreater(len(listnamespaceresult), 0)

        # Get Created Namespace list by ResourceGroup
        listnamespacebyresourcegroupresult = self.cmd('servicebus namespace list --resource-group {rg}').output
        self.assertGreater(len(listnamespacebyresourcegroupresult), 0)

        # Create Authoriazation Rule
        self.cmd(
            'servicebus namespace authorization-rule create --resource-group {rg} --namespace-name {namespacename} --name {authoname} --rights {accessrights}',
            checks=[self.check('name', '{authoname}')])

        # Get Authorization Rule
        self.cmd(
            'servicebus namespace authorization-rule show --resource-group {rg} --namespace-name {namespacename} --name {authoname}',
            checks=[self.check('name', '{authoname}')])

        # Update Authoriazation Rule
        self.cmd(
            'servicebus namespace authorization-rule create --resource-group {rg} --namespace-name {namespacename} --name {authoname} --rights {accessrights1}',
            checks=[self.check('name', '{authoname}')])

        # Get Default Authorization Rule
        self.cmd(
            'servicebus namespace authorization-rule show --resource-group {rg} --namespace-name {namespacename} --name {defaultauthorizationrule}',
            checks=[self.check('name', self.kwargs['defaultauthorizationrule'])])

        # Get Authorization Rule Listkeys
        self.cmd(
            'servicebus namespace authorization-rule keys list --resource-group {rg} --namespace-name {namespacename} --name {authoname}')

        # Regeneratekeys - Primary
        self.cmd(
            'servicebus namespace authorization-rule keys renew --resource-group {rg} --namespace-name {namespacename} --name {authoname} --key {primary}')

        # Regeneratekeys - Secondary
        self.cmd(
            'servicebus namespace authorization-rule keys renew --resource-group {rg} --namespace-name {namespacename} --name {authoname} --key {secondary}')

        # Delete Authorization Rule
        self.cmd(
            'servicebus namespace authorization-rule delete --resource-group {rg} --namespace-name {namespacename} --name {authoname}')

        # Delete Namespace list by ResourceGroup
        self.cmd('servicebus namespace delete --resource-group {rg} --name {namespacename}')

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

    @ResourceGroupPreparer(name_prefix='cli_test_sb_topic')
    def test_sb_topic(self, resource_group):
        self.kwargs.update({
            'namespacename': self.create_random_name(prefix='sb-nscli', length=20),
            'tags': {'tag1: value1', 'tag2: value2'},
            'sku': 'Premium',
            'tier': 'Premium',
            'authoname': self.create_random_name(prefix='cliAutho', length=20),
            'defaultauthorizationrule': 'RootManageSharedAccessKey',
            'accessrights': 'Send',
            'accessrights1': 'Listen',
            'primary': 'PrimaryKey',
            'secondary': 'SecondaryKey',
            'topicname': self.create_random_name(prefix='sb-topiccli', length=25),
            'topicauthoname': self.create_random_name(prefix='cliTopicAutho', length=25)
        })

        # Create Namespace
        self.cmd(
            'servicebus namespace create --resource-group {rg} --name {namespacename} --tags {tags} --sku {sku}',
            checks=[self.check('sku.name', '{sku}')])

        # Get Created Namespace
        self.cmd('servicebus namespace show --resource-group {rg} --name {namespacename}',
                 checks=[self.check('sku.name', '{sku}')])

        # Create Topic
        self.cmd(
            'servicebus topic create --resource-group {rg} --namespace-name {namespacename} --name {topicname}',
            checks=[self.check('name', '{topicname}')])

        # Get Topic
        self.cmd(
            'servicebus topic show --resource-group {rg} --namespace-name {namespacename} --name {topicname}',
            checks=[self.check('name', '{topicname}')])

        # update Topic
        self.cmd(
            'servicebus topic update --resource-group {rg} --namespace-name {namespacename} --name {topicname} --enable-ordering True',
            checks=[self.check('name', '{topicname}')])

        # Topic List
        self.cmd('servicebus topic list --resource-group {rg} --namespace-name {namespacename}')

        # Create Authoriazation Rule
        self.cmd(
            'servicebus topic authorization-rule create --resource-group {rg} --namespace-name {namespacename} --topic-name {topicname} --name {authoname} --rights {accessrights}',
            checks=[self.check('name', '{authoname}')])

        # Get Create Authorization Rule
        self.cmd(
            'servicebus topic authorization-rule show --resource-group {rg} --namespace-name {namespacename} --topic-name {topicname} --name {authoname}',
            checks=[self.check('name', '{authoname}')])

        # Update Authoriazation Rule
        self.cmd(
            'servicebus topic authorization-rule update --resource-group {rg} --namespace-name {namespacename} --topic-name {topicname} --name {authoname} --rights {accessrights1}',
            checks=[self.check('name', '{authoname}')])

        # Get Authorization Rule Listkeys
        self.cmd(
            'servicebus topic authorization-rule keys list --resource-group {rg} --namespace-name {namespacename} --topic-name {topicname} --name {authoname}')

        # Regeneratekeys - Primary
        self.cmd(
            'servicebus topic authorization-rule keys renew --resource-group {rg} --namespace-name {namespacename} --topic-name {topicname} --name {authoname} --key {primary}')

        # Regeneratekeys - Secondary
        self.cmd(
            'servicebus topic authorization-rule keys renew --resource-group {rg} --namespace-name {namespacename} --topic-name {topicname} --name {authoname} --key {secondary}')

        # Delete Topic Authorization Rule
        self.cmd(
            'servicebus topic authorization-rule delete --resource-group {rg} --namespace-name {namespacename} --topic-name {topicname} --name {authoname}')

        # Delete Topic
        self.cmd('servicebus topic delete --resource-group {rg} --namespace-name {namespacename} --name {topicname}')

    @ResourceGroupPreparer(name_prefix='cli_test_sb_subscription')
    def test_sb_subscription(self, resource_group):
        self.kwargs.update({
            'namespacename': self.create_random_name(prefix='sb-nscli', length=20),
            'tags': {'tag1: value1', 'tag2: value2'},
            'sku': 'Standard',
            'tier': 'Standard',
            'authoname': self.create_random_name(prefix='cliAutho', length=20),
            'defaultauthorizationrule': 'RootManageSharedAccessKey',
            'accessrights': 'Send, Listen',
            'primary': 'PrimaryKey',
            'secondary': 'SecondaryKey',
            'topicname': self.create_random_name(prefix='sb-topiccli', length=25),
            'topicauthoname': self.create_random_name(prefix='cliTopicAutho', length=25),
            'subscriptionname': self.create_random_name(prefix='sb-subscli', length=25),
            'lockduration': 'PT3M'
        })

        # Create Namespace
        self.cmd(
            'servicebus namespace create --resource-group {rg} --name {namespacename} --tags {tags} --sku {sku}',
            checks=[self.check('sku.name', '{sku}')])

        # Get Created Namespace
        self.cmd('servicebus namespace show --resource-group {rg} --name {namespacename}',
                 checks=[self.check('sku.name', '{sku}')])

        # Create Topic
        self.cmd('servicebus topic create --resource-group {rg} --namespace-name {namespacename} --name {topicname}',
                 checks=[self.check('name', '{topicname}')])

        # Get Topic
        self.cmd('servicebus topic show --resource-group {rg} --namespace-name {namespacename} --name {topicname}',
                 checks=[self.check('name', '{topicname}')])

        # Create Subscription
        self.cmd(
            'servicebus topic subscription create --resource-group {rg} --namespace-name {namespacename} --topic-name {topicname} --name {subscriptionname}',
            checks=[self.check('name', '{subscriptionname}')])

        # Get Create Subscription
        self.cmd(
            'servicebus topic subscription show --resource-group {rg} --namespace-name {namespacename} --topic-name {topicname} --name {subscriptionname}',
            checks=[self.check('name', '{subscriptionname}')])

        # Get list of Subscription+
        self.cmd(
            'servicebus topic subscription list --resource-group {rg} --namespace-name {namespacename} --topic-name {topicname}')

        # update Subscription
        self.cmd(
            'servicebus topic subscription update --resource-group {rg} --namespace-name {namespacename} --topic-name {topicname} --name {subscriptionname} --lock-duration {lockduration}',
            checks=[self.check('name', '{subscriptionname}')])

        # Delete Subscription
        self.cmd(
            'servicebus topic subscription delete --resource-group {rg} --namespace-name {namespacename} --topic-name {topicname} --name {subscriptionname}')

        # Delete Topic
        self.cmd('servicebus topic delete --resource-group {rg} --namespace-name {namespacename} --name {topicname}')

        # Delete Namespace
        self.cmd('servicebus namespace delete --resource-group {rg} --name {namespacename}')

    @ResourceGroupPreparer(name_prefix='cli_test_sb_rules')
    def test_sb_rules(self, resource_group):
        self.kwargs.update({
            'namespacename': self.create_random_name(prefix='sb-nscli', length=20),
            'tags': {'tag1: value1', 'tag2: value2'},
            'sku': 'Standard',
            'tier': 'Standard',
            'authoname': self.create_random_name(prefix='cliAutho', length=20),
            'defaultauthorizationrule': 'RootManageSharedAccessKey',
            'accessrights': 'Listen',
            'primary': 'PrimaryKey',
            'secondary': 'SecondaryKey',
            'topicname': self.create_random_name(prefix='sb-topiccli', length=25),
            'topicauthoname': self.create_random_name(prefix='cliTopicAutho', length=25),
            'subscriptionname': self.create_random_name(prefix='sb-subscli', length=25),
            'rulename': self.create_random_name(prefix='sb-rulecli', length=25),
            'sqlexpression': 'test=test',
            'sqlexpression1': 'test1=test1'
        })

        # Create Namespace
        self.cmd(
            'servicebus namespace create --resource-group {rg} --name {namespacename} --tags {tags} --sku {sku}',
            checks=[self.check('sku.name', '{sku}')])

        # Get Created Namespace
        self.cmd('servicebus namespace show --resource-group {rg} --name {namespacename}',
                 checks=[self.check('sku.name', '{sku}')])

        # Create Topic
        self.cmd('servicebus topic create --resource-group {rg} --namespace-name {namespacename} --name {topicname} ',
                 checks=[self.check('name', '{topicname}')])

        # Get Topic
        self.cmd('servicebus topic show --resource-group {rg} --namespace-name {namespacename} --name {topicname} ',
                 checks=[self.check('name', '{topicname}')])

        # Create Subscription
        self.cmd(
            'servicebus topic subscription create --resource-group {rg} --namespace-name {namespacename} --topic-name {topicname} --name {subscriptionname}',
            checks=[self.check('name', '{subscriptionname}')])

        # Get Create Subscription
        self.cmd(
            'servicebus topic subscription show --resource-group {rg} --namespace-name {namespacename} --topic-name {topicname} --name {subscriptionname}',
            checks=[self.check('name', '{subscriptionname}')])

        # Create Rules
        self.cmd(
            'servicebus topic subscription rule create --resource-group {rg} --namespace-name {namespacename} --topic-name {topicname} --subscription-name {subscriptionname} --name {rulename} --filter-sql-expression {sqlexpression}',
            checks=[self.check('name', '{rulename}')])

        # Get Created Rules
        self.cmd(
            'servicebus topic subscription rule show --resource-group {rg} --namespace-name {namespacename} --topic-name {topicname} --subscription-name {subscriptionname} --name {rulename}',
            checks=[self.check('name', '{rulename}')])

        # Update Rules
        self.cmd(
            'servicebus topic subscription rule update --resource-group {rg} --namespace-name {namespacename} --topic-name {topicname} --subscription-name {subscriptionname} --name {rulename} --filter-sql-expression {sqlexpression1}',
            checks=[self.check('name', '{rulename}')])

        # Get Rules List By Subscription
        self.cmd(
            'servicebus topic subscription rule list --resource-group {rg} --namespace-name {namespacename} --topic-name {topicname} --subscription-name {subscriptionname}')

        # Delete create rule
        self.cmd(
            'servicebus topic subscription rule delete --resource-group {rg} --namespace-name {namespacename} --topic-name {topicname} --subscription-name {subscriptionname} --name {rulename}')

        # Delete create Subscription
        self.cmd(
            'servicebus topic subscription delete --resource-group {rg} --namespace-name {namespacename} --topic-name {topicname} --name {subscriptionname}')

        # Delete Topic
        self.cmd('servicebus topic delete --resource-group {rg} --namespace-name {namespacename} --name {topicname}')

        # Delete Namespace
        self.cmd('servicebus namespace delete --resource-group {rg} --name {namespacename}')

    @ResourceGroupPreparer(name_prefix='cli_test_sb_alias')
    def test_sb_alias(self, resource_group):
        from azure.mgmt.servicebus.models import ProvisioningStateDR
        self.kwargs.update({
            'loc_south': 'SouthCentralUS',
            'loc_north': 'NorthCentralUS',
            'namespacenameprimary': self.create_random_name(prefix='sb-nscli', length=20),
            'namespacenamesecondary': self.create_random_name(prefix='sb-nscli', length=20),
            'tags': {'tag1: value1', 'tag2: value2'},
            'sku': 'Premium',
            'tier': 'Premium',
            'authoname': self.create_random_name(prefix='cliAutho', length=20),
            'defaultauthorizationrule': 'RootManageSharedAccessKey',
            'accessrights': 'Send',
            'primary': 'PrimaryKey',
            'secondary': 'SecondaryKey',
            'aliasname': self.create_random_name(prefix='cliAlias', length=20),
            'alternatename': self.create_random_name(prefix='cliAlter', length=20),
            'id': '',
            'test': ''
        })

        self.cmd('servicebus namespace exists --name {namespacenameprimary}',
                 checks=[self.check('nameAvailable', True)])

        # Create Namespace - Primary
        self.cmd(
            'servicebus namespace create --resource-group {rg} --name {namespacenameprimary} --location {loc_south} --tags {tags} --sku {sku}',
            checks=[self.check('sku.name', '{sku}')])

        # Get Created Namespace - Primary
        self.cmd('servicebus namespace show --resource-group {rg} --name {namespacenameprimary}',
                 checks=[self.check('sku.name', '{sku}')])

        # Create Namespace - Secondary
        self.cmd(
            'servicebus namespace create --resource-group {rg} --name {namespacenamesecondary} --location {loc_north} --tags {tags} --sku {sku}',
            checks=[self.check('sku.name', '{sku}')])

        # Get Created Namespace - Secondary
        getnamespace2result = self.cmd(
            'servicebus namespace show --resource-group {rg} --name {namespacenamesecondary}',
            checks=[self.check('sku.name', '{sku}')]).get_output_in_json()

        # Create Authoriazation Rule
        self.cmd(
            'servicebus namespace authorization-rule create --resource-group {rg} --namespace-name {namespacenameprimary} --name {authoname} --rights {accessrights}',
            checks=[self.check('name', '{authoname}')])

        partnernamespaceid = getnamespace2result['id']
        self.kwargs.update({'id': partnernamespaceid})
        # Get Create Authorization Rule
        self.cmd(
            'servicebus namespace authorization-rule show --resource-group {rg} --namespace-name {namespacenameprimary} --name {authoname}',
            checks=[self.check('name', '{authoname}')])

        # CheckNameAvailability - Alias

        self.cmd(
            'servicebus georecovery-alias exists --resource-group {rg} --namespace-name {namespacenameprimary} --alias {aliasname}',
            checks=[self.check('nameAvailable', True)])

        # Create alias
        self.cmd(
            'servicebus georecovery-alias set  --resource-group {rg} --namespace-name {namespacenameprimary} -a {aliasname} --partner-namespace {namespacenamesecondary}')

        # get alias - Primary
        self.cmd(
            'servicebus georecovery-alias show  --resource-group {rg} --namespace-name {namespacenameprimary} --alias {aliasname}')

        # get alias - Secondary
        self.cmd(
            'servicebus georecovery-alias show  --resource-group {rg} --namespace-name {namespacenamesecondary} --alias {aliasname}')

        getaliasprimarynamespace = self.cmd(
            'servicebus georecovery-alias show  --resource-group {rg} --namespace-name {namespacenameprimary} --alias {aliasname}').get_output_in_json()

        # check for the Alias Provisioning succeeded
        while getaliasprimarynamespace['provisioningState'] != ProvisioningStateDR.succeeded.value:
            time.sleep(30)
            getaliasprimarynamespace = self.cmd(
                'servicebus georecovery-alias show  --resource-group {rg} --namespace-name {namespacenameprimary} --alias {aliasname}').get_output_in_json()

        # Get Authorization Rule
        self.cmd(
            'servicebus georecovery-alias authorization-rule show --resource-group {rg} --namespace-name {namespacenameprimary} --alias {aliasname} --name {authoname}',
            checks=[self.check('name', '{authoname}')])

        # Get Authorization Rule Keys
        self.cmd(
            'servicebus georecovery-alias authorization-rule keys list --resource-group {rg} --namespace-name {namespacenameprimary} --alias {aliasname} --name {authoname}')

        # Get available Authorization Rules
        self.cmd(
            'servicebus georecovery-alias authorization-rule list --resource-group {rg} --namespace-name {namespacenameprimary} --alias {aliasname}')

        # Break Pairing
        self.cmd(
            'servicebus georecovery-alias break-pair  --resource-group {rg} --namespace-name {namespacenameprimary} --alias {aliasname}')

        getaliasafterbreak = self.cmd(
            'servicebus georecovery-alias show  --resource-group {rg} --namespace-name {namespacenameprimary} --alias {aliasname}').get_output_in_json()

        # check for the Alias Provisioning succeeded
        while getaliasafterbreak['provisioningState'] != ProvisioningStateDR.succeeded.value:
            time.sleep(30)
            getaliasafterbreak = self.cmd(
                'servicebus georecovery-alias show  --resource-group {rg} --namespace-name {namespacenameprimary} --alias {aliasname}').get_output_in_json()

        # Create alias
        self.cmd(
            'servicebus georecovery-alias set  --resource-group {rg} --namespace-name {namespacenameprimary} --alias {aliasname} --partner-namespace {id}')

        getaliasaftercreate = self.cmd(
            'servicebus georecovery-alias show  --resource-group {rg} --namespace-name {namespacenameprimary} --alias {aliasname}').get_output_in_json()

        # check for the Alias Provisioning succeeded
        while getaliasaftercreate['provisioningState'] != ProvisioningStateDR.succeeded.value:
            time.sleep(30)
            getaliasaftercreate = self.cmd(
                'servicebus georecovery-alias show  --resource-group {rg} --namespace-name {namespacenameprimary} --alias {aliasname}').get_output_in_json()

        # FailOver
        self.cmd(
            'servicebus georecovery-alias fail-over  --resource-group {rg} --namespace-name {namespacenamesecondary} --alias {aliasname}')

        getaliasafterfail = self.cmd(
            'servicebus georecovery-alias show  --resource-group {rg} --namespace-name {namespacenamesecondary} --alias {aliasname}').get_output_in_json()

        # check for the Alias Provisioning succeeded
        while getaliasafterfail['provisioningState'] != ProvisioningStateDR.succeeded.value:
            time.sleep(30)
            getaliasafterfail = self.cmd(
                'servicebus georecovery-alias show  --resource-group {rg} --namespace-name {namespacenamesecondary} --alias {aliasname}').get_output_in_json()

        # Delete Alias
        self.cmd(
            'servicebus georecovery-alias delete  --resource-group {rg} --namespace-name {namespacenamesecondary} --alias {aliasname}')

        time.sleep(30)

        # Delete Namespace - primary
        self.cmd('servicebus namespace delete --resource-group {rg} --name {namespacenameprimary}')

        # Delete Namespace - secondary
        self.cmd('servicebus namespace delete --resource-group {rg} --name {namespacenamesecondary}')

        # Test playback fails and the live-only flag will be removed once it is addressed

    @live_only()
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

        # Delete Namespace - Premium
        self.cmd('servicebus namespace delete --resource-group {rg} --name {namespacenamepremium}')

    @ResourceGroupPreparer(name_prefix='cli_test_sb_network')
    def test_sb_network(self, resource_group):
        self.kwargs.update({
            'namespacename': self.create_random_name(prefix='servicebus-cli', length=20),
            'namespacenamekafka': self.create_random_name(prefix='servicebus-cli1', length=20),
            'tags': {'tag1=value1'},
            'tags2': {'tag2=value2'},
            'sku': 'Premium',
            'tier': 'Premium',
            'authoname': self.create_random_name(prefix='cliAutho', length=20),
            'defaultauthorizationrule': 'RootManageSharedAccessKey',
            'accessrights': 'Send',
            'namevnet': 'sbehvnettest1',
            'namevnet1': 'sbehvnettest2',
            'namesubnet1': 'default',
            'namesubnet2': 'secondvnet',
            'isautoinflateenabled': 'True',
            'maximumthroughputunits': 4,
            'maximumthroughputunits_update': 5,
            'varfalse': 'false',
            'ipmask1': '1.1.1.1',
            'ipmask2': '2.2.2.2'
        })

        self.cmd('network vnet create --resource-group {rg} --name {namevnet}')
        self.cmd('network vnet create --resource-group {rg} --name {namevnet1}')

        created_subnet1 = self.cmd(
            'network vnet subnet create --resource-group {rg} --name {namesubnet1} --vnet-name {namevnet} --address-prefixes 10.0.0.0/24').get_output_in_json()
        created_subnet2 = self.cmd(
            'network vnet subnet create --resource-group {rg} --name {namesubnet2} --vnet-name {namevnet1} --address-prefixes 10.0.0.0/24').get_output_in_json()

        # Check for the NameSpace name Availability
        self.cmd('servicebus namespace exists --name {namespacename}',
                 checks=[self.check('nameAvailable', True)])

        # Create Namespace
        self.cmd(
            'servicebus namespace create --resource-group {rg} --name {namespacename} --tags {tags} --sku {sku} --default-action Allow',
            checks=[self.check('sku.name', '{sku}')])

        # Get Created Namespace
        self.cmd('servicebus namespace show --resource-group {rg} --name {namespacename}',
                 checks=[self.check('sku.name', '{sku}')])

        # Update Namespace
        self.cmd(
            'servicebus namespace update --resource-group {rg} --name {namespacename} --tags {tags} --default-action Deny',
            checks=[self.check('sku.name', '{sku}')])

        # Get NetworkRule
        self.cmd(
            'servicebus namespace network-rule list --resource-group {rg} --name {namespacename}').get_output_in_json()

        # add IP Rule
        iprule = self.cmd(
            'servicebus namespace network-rule add --resource-group {rg} --name {namespacename} --ip-address {ipmask1} --action Allow').get_output_in_json()
        self.assertEqual(len(iprule['ipRules']), 1)

        # add IP Rule
        iprule = self.cmd(
            'servicebus namespace network-rule add --resource-group {rg} --name {namespacename} --ip-address {ipmask2} --action Allow').get_output_in_json()
        self.assertEqual(len(iprule['ipRules']), 2)
        self.assertTrue(iprule['ipRules'][0]['ipMask'] == '1.1.1.1')
        self.assertTrue(iprule['ipRules'][1]['ipMask'] == '2.2.2.2')

        # Get list of IP rule
        iprule = self.cmd(
            'servicebus namespace network-rule list --resource-group {rg} --name {namespacename}').get_output_in_json()
        self.assertEqual(len(iprule['ipRules']), 2)

        # Remove IPRule
        iprule = self.cmd(
            'servicebus namespace network-rule remove --resource-group {rg} --name {namespacename} --ip-address {ipmask2}').get_output_in_json()
        self.assertEqual(len(iprule['ipRules']), 1)
        self.assertTrue(iprule['ipRules'][0]['ipMask'] == '1.1.1.1')

        # add vnetrule
        vnetrule = self.cmd(
            'servicebus namespace network-rule add --resource-group {rg} --name {namespacename} --subnet ' +
            created_subnet1['id'] + ' --ignore-missing-endpoint True').get_output_in_json()
        self.assertEqual(len(vnetrule['virtualNetworkRules']), 1)

        # add vnetrule2
        vnetrule = self.cmd(
            'servicebus namespace network-rule add --resource-group {rg} --name {namespacename} --subnet ' +
            created_subnet2['id'] + ' --ignore-missing-endpoint True').get_output_in_json()
        self.assertEqual(len(vnetrule['virtualNetworkRules']), 2)

        # list Vnetrules
        self.cmd(
            'servicebus namespace network-rule list --resource-group {rg} --name {namespacename}')

        # remove Vnetrule
        vnetrule = self.cmd(
            'servicebus namespace network-rule remove --resource-group {rg} --name {namespacename} --subnet ' +
            created_subnet2['id']).get_output_in_json()
        self.assertEqual(len(vnetrule['virtualNetworkRules']), 1)

        # Delete Namespace list by ResourceGroup
        self.cmd('servicebus namespace delete --resource-group {rg} --name {namespacename}')
