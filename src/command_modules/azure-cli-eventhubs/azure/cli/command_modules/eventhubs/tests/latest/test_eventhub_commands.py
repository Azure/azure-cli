# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# AZURE CLI EventHub - NAMESPACE TEST DEFINITIONS

import time

from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer)


# pylint: disable=line-too-long
# pylint: disable=too-many-lines


class EHNamespaceCURDScenarioTest(ScenarioTest):
    from azure_devtools.scenario_tests import AllowLargeResponse

    @AllowLargeResponse()
    @ResourceGroupPreparer(name_prefix='cli_test_eh_namespace')
    def test_eh_namespace(self, resource_group):
        self.kwargs.update({
            'loc': 'westus',
            'rg': resource_group,
            'namespacename': self.create_random_name(prefix='eventhubs-nscli', length=20),
            'namespacenamekafka': self.create_random_name(prefix='eventhubs-nscli1', length=20),
            'tags': {'tag1=value1'},
            'tags2': {'tag2=value2'},
            'sku': 'Standard',
            'tier': 'Standard',
            'authoname': self.create_random_name(prefix='cliAutho', length=20),
            'defaultauthorizationrule': 'RootManageSharedAccessKey',
            'accessrights': 'Send',
            'accessrights1': 'Listen',
            'primary': 'PrimaryKey',
            'secondary': 'SecondaryKey',
            'isautoinflateenabled': 'True',
            'maximumthroughputunits': 4,
            'maximumthroughputunits_update': 5
        })

        # Check for the NameSpace name Availability

        self.cmd('eventhubs namespace exists --name {namespacename}',
                 checks=[self.check('nameAvailable', True)])

        # Create kafka Namespace
        self.cmd('eventhubs namespace create --resource-group {rg} --name {namespacenamekafka} --location {loc} --tags {tags} --sku {sku} --enable-auto-inflate {isautoinflateenabled} --maximum-throughput-units {maximumthroughputunits} --enable-kafka {isautoinflateenabled}',
                 checks=[self.check('kafkaEnabled', True)])

        # Create Namespace
        self.cmd(
            'eventhubs namespace create --resource-group {rg} --name {namespacename} --location {loc} --tags {tags} --sku {sku} --enable-auto-inflate {isautoinflateenabled} --maximum-throughput-units {maximumthroughputunits}',
            checks=[self.check('sku.name', self.kwargs['sku'])])

        # Get Created Namespace
        self.cmd('eventhubs namespace show --resource-group {rg} --name {namespacename}',
                 checks=[self.check('sku.name', self.kwargs['sku'])])

        # Update Namespace
        self.cmd(
            'eventhubs namespace update --resource-group {rg} --name {namespacename} --tags {tags2} --maximum-throughput-units {maximumthroughputunits_update}',
            checks=[self.check('sku.name', self.kwargs['sku'])])

        # Get Created Namespace list by subscription
        listnamespaceresult = self.cmd('eventhubs namespace list').output
        self.assertGreater(len(listnamespaceresult), 0)

        # Get Created Namespace list by ResourceGroup
        listnamespacebyresourcegroupresult = self.cmd('eventhubs namespace list --resource-group {rg}').output
        self.assertGreater(len(listnamespacebyresourcegroupresult), 0)

        # Create Authoriazation Rule
        self.cmd('eventhubs namespace authorization-rule create --resource-group {rg} --namespace-name {namespacename} --name {authoname} --rights {accessrights}',
                 checks=[self.check('name', self.kwargs['authoname'])])

        # Get Authorization Rule
        self.cmd('eventhubs namespace authorization-rule show --resource-group {rg} --namespace-name {namespacename} --name {authoname}', checks=[self.check('name', self.kwargs['authoname'])])

        # Update Authoriazation Rule
        self.cmd(
            'eventhubs namespace authorization-rule update --resource-group {rg} --namespace-name {namespacename} --name {authoname} --rights {accessrights1}',
            checks=[self.check('name', self.kwargs['authoname'])])

        # Get Default Authorization Rule
        self.cmd('eventhubs namespace authorization-rule show --resource-group {rg} --namespace-name {namespacename} --name {defaultauthorizationrule}',
                 checks=[self.check('name', self.kwargs['defaultauthorizationrule'])])

        # Get Authorization Rule Listkeys
        self.cmd('eventhubs namespace authorization-rule keys list --resource-group {rg} --namespace-name {namespacename} --name {authoname}')

        # Regeneratekeys - Primary
        self.cmd(
            'eventhubs namespace authorization-rule keys renew --resource-group {rg} --namespace-name {namespacename} --name {authoname} --key {primary}')

        # Regeneratekeys - Secondary
        self.cmd('eventhubs namespace authorization-rule keys renew --resource-group {rg} --namespace-name {namespacename} --name {authoname} --key {secondary}')

        # Delete Authorization Rule
        self.cmd('eventhubs namespace authorization-rule delete --resource-group {rg} --namespace-name {namespacename} --name {authoname}')

        # Delete Namespace list by ResourceGroup
        self.cmd('eventhubs namespace delete --resource-group {rg} --name {namespacename}')

    @ResourceGroupPreparer(name_prefix='cli_test_eh_eventnhub')
    def test_eh_eventhub(self, resource_group):
        self.kwargs.update({
            'loc': 'westus2',
            'rg': resource_group,
            'namespacename': self.create_random_name(prefix='eventhubs-nscli', length=20),
            'tags': {'tag1: value1', 'tag2: value2'},
            'sku': 'Standard',
            'tier': 'Standard',
            'authoname': self.create_random_name(prefix='cliAutho', length=20),
            'defaultauthorizationrule': 'RootManageSharedAccessKey',
            'accessrights': 'Listen',
            'accessrights1': 'Send',
            'primary': 'PrimaryKey',
            'secondary': 'SecondaryKey',
            'eventhubname': self.create_random_name(prefix='eventhubs-eventhubcli', length=25),
            'eventhubauthoname': self.create_random_name(prefix='cliEventAutho', length=25),
            'isautoinflateenabled': 'True',
            'maximumthroughputunits': 4,
            'messageretentionindays': 4,
            'partitioncount': 4
        })

        # Create Namespace
        self.cmd(
            'eventhubs namespace create --resource-group {rg} --name {namespacename} --location {loc} --tags {tags} --sku {sku} --enable-auto-inflate {isautoinflateenabled} --maximum-throughput-units {maximumthroughputunits}',
            checks=[self.check('sku.name', self.kwargs['sku'])])

        # Get Created Namespace
        self.cmd('eventhubs namespace show --resource-group {rg} --name {namespacename}',
                 checks=[self.check('sku.name', self.kwargs['sku'])])

        # Create Eventhub
        self.cmd(
            'eventhubs eventhub create --resource-group {rg} --namespace-name {namespacename} --name {eventhubname}',
            checks=[self.check('name', self.kwargs['eventhubname'])])

        # Get Eventhub
        self.cmd('eventhubs eventhub show --resource-group {rg} --namespace-name {namespacename} --name {eventhubname}',
                 checks=[self.check('name', self.kwargs['eventhubname'])])

        # update Eventhub
        self.cmd(
            'eventhubs eventhub update --resource-group {rg} --namespace-name {namespacename} --name {eventhubname} --partition-count {partitioncount} --message-retention {messageretentionindays}',
            checks=[self.check('name', self.kwargs['eventhubname'])])

        # Eventhub List
        listeventhub = self.cmd('eventhubs eventhub list --resource-group {rg} --namespace-name {namespacename}').output
        self.assertGreater(len(listeventhub), 0)

        # Create Authoriazation Rule
        self.cmd(
            'eventhubs eventhub authorization-rule create --resource-group {rg} --namespace-name {namespacename} --eventhub-name {eventhubname} --name {authoname} --rights {accessrights}',
            checks=[self.check('name', self.kwargs['authoname'])])

        # Get Create Authorization Rule
        self.cmd(
            'eventhubs eventhub authorization-rule show --resource-group {rg} --namespace-name {namespacename} --eventhub-name {eventhubname} --name {authoname}',
            checks=[self.check('name', self.kwargs['authoname'])])

        # update Authoriazation Rule
        self.cmd(
            'eventhubs eventhub authorization-rule update --resource-group {rg} --namespace-name {namespacename} --eventhub-name {eventhubname} --name {authoname} --rights {accessrights1}',
            checks=[self.check('name', self.kwargs['authoname'])])

        # Get Authorization Rule Listkeys
        self.cmd(
            'eventhubs eventhub authorization-rule keys list --resource-group {rg} --namespace-name {namespacename} --eventhub-name {eventhubname} --name {authoname}')

        # Regeneratekeys - Primary
        regenrateprimarykeyresult = self.cmd(
            'eventhubs eventhub authorization-rule keys renew --resource-group {rg} --namespace-name {namespacename} --eventhub-name {eventhubname} --name {authoname} --key {primary}')
        self.assertIsNotNone(regenrateprimarykeyresult)

        # Regeneratekeys - Secondary
        regenratesecondarykeyresult = self.cmd(
            'eventhubs eventhub authorization-rule keys renew --resource-group {rg} --namespace-name {namespacename} --eventhub-name {eventhubname} --name {authoname} --key {secondary}')
        self.assertIsNotNone(regenratesecondarykeyresult)

        # Delete Eventhub AuthorizationRule
        self.cmd(
            'eventhubs eventhub authorization-rule delete --resource-group {rg} --namespace-name {namespacename} --eventhub-name {eventhubname} --name {authoname}')

        # Delete Eventhub
        self.cmd(
            'eventhubs eventhub delete --resource-group {rg} --namespace-name {namespacename} --name {eventhubname}')

        # Delete Namespace
        self.cmd('eventhubs namespace delete --resource-group {rg} --name {namespacename}')

    @ResourceGroupPreparer(name_prefix='cli_test_eh_consumergroup')
    def test_eh_consumergroup(self, resource_group):
        self.kwargs.update({
            'loc': 'westus2',
            'rg': resource_group,
            'namespacename': self.create_random_name(prefix='eventhubs-nscli', length=20),
            'tags': {'tag1: value1', 'tag2: value2'},
            'sku': 'Standard',
            'tier': 'Standard',
            'eventhubname': self.create_random_name(prefix='eventhubs-eventhubcli', length=25),
            'isautoinflateenabled': 'True',
            'maximumthroughputunits': 4,
            'consumergroupname': self.create_random_name(prefix='clicg', length=20),
            'usermetadata1': 'usermetadata',
            'usermetadata2': 'usermetadata-updated'
        })

        # Create Namespace
        self.cmd('eventhubs namespace create --resource-group {rg} --name {namespacename} --location {loc} --tags {tags} --sku {sku} --enable-auto-inflate {isautoinflateenabled} --maximum-throughput-units {maximumthroughputunits}',
                 checks=[self.check('sku.name', self.kwargs['sku'])])

        # Get Created Namespace
        self.cmd('eventhubs namespace show --resource-group {rg} --name {namespacename}', checks=[self.check('sku.name', self.kwargs['sku'])])

        # Create Eventhub
        self.cmd('eventhubs eventhub create --resource-group {rg} --namespace-name {namespacename} --name {eventhubname}', checks=[self.check('name', self.kwargs['eventhubname'])])

        # Get Eventhub
        self.cmd('eventhubs eventhub show --resource-group {rg} --namespace-name {namespacename} --name {eventhubname}', checks=[self.check('name', self.kwargs['eventhubname'])])

        # Create ConsumerGroup
        self.cmd('eventhubs eventhub consumer-group create --resource-group {rg} --namespace-name {namespacename} --eventhub-name {eventhubname} --name {consumergroupname} --user-metadata {usermetadata1}', checks=[self.check('name', self.kwargs['consumergroupname'])])

        # Get Consumer Group
        self.cmd('eventhubs eventhub consumer-group show --resource-group {rg} --namespace-name {namespacename} --eventhub-name {eventhubname} --name {consumergroupname}', checks=[self.check('name', self.kwargs['consumergroupname'])])

        # Update ConsumerGroup
        self.cmd('eventhubs eventhub consumer-group update --resource-group {rg} --namespace-name {namespacename} --eventhub-name {eventhubname} --name {consumergroupname} --user-metadata {usermetadata2}', checks=[self.check('userMetadata', self.kwargs['usermetadata2'])])

        # Get ConsumerGroup List
        listconsumergroup = self.cmd('eventhubs eventhub consumer-group list --resource-group {rg} --namespace-name {namespacename} --eventhub-name {eventhubname}').output
        self.assertGreater(len(listconsumergroup), 0)

        # Delete ConsumerGroup
        self.cmd('eventhubs eventhub consumer-group delete --resource-group {rg} --namespace-name {namespacename} --eventhub-name {eventhubname} --name {consumergroupname}')

        # Delete Eventhub
        self.cmd('eventhubs eventhub delete --resource-group {rg} --namespace-name {namespacename} --name {eventhubname}')

        # Delete Namespace
        self.cmd('eventhubs namespace delete --resource-group {rg} --name {namespacename}')

    @ResourceGroupPreparer(name_prefix='cli_test_eh_alias')
    def test_eh_alias(self, resource_group):
        from azure.mgmt.eventhub.models import ProvisioningStateDR
        self.kwargs.update({
            'loc_south': 'SouthCentralUS',
            'loc_north': 'NorthCentralUS',
            'rg': resource_group,
            'namespacenameprimary': self.create_random_name(prefix='eh-nscli', length=20),
            'namespacenamesecondary': self.create_random_name(prefix='eh-nscli', length=20),
            'tags': {'tag1: value1', 'tag2: value2'},
            'sku': 'Standard',
            'tier': 'Standard',
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

        self.cmd('eventhubs namespace exists --name {namespacenameprimary}',
                 checks=[self.check('nameAvailable', True)])

        # Create Namespace - Primary
        self.cmd('eventhubs namespace create --resource-group {rg} --name {namespacenameprimary} --location {loc_south} --tags {tags} --sku {sku}', checks=[self.check('sku.name', self.kwargs['sku'])])

        # Get Created Namespace - Primary
        self.cmd('eventhubs namespace show --resource-group {rg} --name {namespacenameprimary}', checks=[self.check('sku.name', self.kwargs['sku'])])

        # Create Namespace - Secondary
        self.cmd('eventhubs namespace create --resource-group {rg} --name {namespacenamesecondary} --location {loc_north} --tags {tags} --sku {sku}', checks=[self.check('sku.name', self.kwargs['sku'])])

        # Get Created Namespace - Secondary
        getnamespace2result = self.cmd('eventhubs namespace show --resource-group {rg} --name {namespacenamesecondary}', checks=[self.check('sku.name', self.kwargs['sku'])]).get_output_in_json()

        # Create Authoriazation Rule
        self.cmd('eventhubs namespace authorization-rule create --resource-group {rg} --namespace-name {namespacenameprimary} --name {authoname} --rights {accessrights}', checks=[self.check('name', self.kwargs['authoname'])])

        partnernamespaceid = getnamespace2result['id']
        self.kwargs.update({'id': partnernamespaceid})
        # Get Create Authorization Rule
        self.cmd('eventhubs namespace authorization-rule show --resource-group {rg} --namespace-name {namespacenameprimary} --name {authoname}', checks=[self.check('name', self.kwargs['authoname'])])

        # CheckNameAvailability - Alias

        self.cmd('eventhubs georecovery-alias exists --resource-group {rg} --namespace-name {namespacenameprimary} --alias {aliasname}', checks=[self.check('nameAvailable', True)])

        # Create alias
        self.cmd('eventhubs georecovery-alias set  --resource-group {rg} --namespace-name {namespacenameprimary} --alias {aliasname} --partner-namespace {id}')

        # get alias - Primary
        self.cmd('eventhubs georecovery-alias show  --resource-group {rg} --namespace-name {namespacenameprimary} --alias {aliasname}')

        # get alias - Secondary
        self.cmd('eventhubs georecovery-alias show  --resource-group {rg} --namespace-name {namespacenamesecondary} --alias {aliasname}')

        getaliasprimarynamespace = self.cmd('eventhubs georecovery-alias show  --resource-group {rg} --namespace-name {namespacenameprimary} --alias {aliasname}').get_output_in_json()

        # Get Authorization Rule
        self.cmd('eventhubs georecovery-alias authorization-rule show --resource-group {rg} --namespace-name {namespacenameprimary} --alias {aliasname} --name {authoname}', checks=[self.check('name', self.kwargs['authoname'])])

        # Get Default Authorization Rule
        self.cmd('eventhubs georecovery-alias authorization-rule list --resource-group {rg} --namespace-name {namespacenameprimary} --alias {aliasname}')

        # check for the Alias Provisioning succeeded
        while getaliasprimarynamespace['provisioningState'] != ProvisioningStateDR.succeeded.value:
            time.sleep(30)
            getaliasprimarynamespace = self.cmd('eventhubs georecovery-alias show  --resource-group {rg} --namespace-name {namespacenameprimary} --alias {aliasname}').get_output_in_json()

        while getaliasprimarynamespace['pendingReplicationOperationsCount'] != 0 and getaliasprimarynamespace['pendingReplicationOperationsCount'] is not None:
            time.sleep(30)
            getaliasprimarynamespace = self.cmd(
                'eventhubs georecovery-alias show  --resource-group {rg} --namespace-name {namespacenameprimary} --alias {aliasname}').get_output_in_json()

        # Break Pairing
        self.cmd('eventhubs georecovery-alias break-pair  --resource-group {rg} --namespace-name {namespacenameprimary} --alias {aliasname}')

        getaliasafterbreak = self.cmd('eventhubs georecovery-alias show  --resource-group {rg} --namespace-name {namespacenameprimary} --alias {aliasname}').get_output_in_json()

        # check for the Alias Provisioning succeeded
        while getaliasafterbreak['provisioningState'] != ProvisioningStateDR.succeeded.value:
            time.sleep(30)
            getaliasafterbreak = self.cmd('eventhubs georecovery-alias show  --resource-group {rg} --namespace-name {namespacenameprimary} --alias {aliasname}').get_output_in_json()

        # Create alias
        self.cmd('eventhubs georecovery-alias set  --resource-group {rg} --namespace-name {namespacenameprimary} --alias {aliasname} --partner-namespace {id}')

        getaliasaftercreate = self.cmd('eventhubs georecovery-alias show  --resource-group {rg} --namespace-name {namespacenameprimary} --alias {aliasname}').get_output_in_json()

        # check for the Alias Provisioning succeeded
        while getaliasaftercreate['provisioningState'] != ProvisioningStateDR.succeeded.value:
            time.sleep(30)
            getaliasaftercreate = self.cmd('eventhubs georecovery-alias show  --resource-group {rg} --namespace-name {namespacenameprimary} --alias {aliasname}').get_output_in_json()

        while getaliasaftercreate['pendingReplicationOperationsCount'] != 0 and getaliasaftercreate['pendingReplicationOperationsCount'] is not None:
            time.sleep(30)
            getaliasaftercreate = self.cmd(
                'eventhubs georecovery-alias show  --resource-group {rg} --namespace-name {namespacenameprimary} --alias {aliasname}').get_output_in_json()

        # FailOver
        self.cmd('eventhubs georecovery-alias fail-over  --resource-group {rg} --namespace-name {namespacenamesecondary} --alias {aliasname}')

        getaliasafterfail = self.cmd('eventhubs georecovery-alias show  --resource-group {rg} --namespace-name {namespacenamesecondary} --alias {aliasname}').get_output_in_json()

        # check for the Alias Provisioning succeeded
        while getaliasafterfail['provisioningState'] != ProvisioningStateDR.succeeded.value:
            time.sleep(30)
            getaliasafterfail = self.cmd('eventhubs georecovery-alias show  --resource-group {rg} --namespace-name {namespacenamesecondary} --alias {aliasname}').get_output_in_json()

        # Delete Alias
        self.cmd('eventhubs georecovery-alias delete  --resource-group {rg} --namespace-name {namespacenamesecondary} --alias {aliasname}')

        time.sleep(30)

        # Delete Namespace - primary
        self.cmd('eventhubs namespace delete --resource-group {rg} --name {namespacenameprimary}')

        time.sleep(30)

        # Delete Namespace - secondary
        self.cmd('eventhubs namespace delete --resource-group {rg} --name {namespacenamesecondary}')
