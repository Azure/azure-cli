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


class SBDRAliasCRUDScenarioTest(ScenarioTest):
    from azure.cli.testsdk.scenario_tests import AllowLargeResponse

    @AllowLargeResponse()
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
