# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure_devtools.scenario_tests import AllowLargeResponse, record_only
from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer, JMESPathCheck)


class SecurityAtpSettingsTests(ScenarioTest):
    @ResourceGroupPreparer()
    @StorageAccountPreparer()
    @record_only()
    def test_security_atp_settings(self, resource_group, resource_group_location, storage_account):
        # run show cli
        self.cmd('security atp show --resource-group {} --storage-account-name {}'
                 .format(resource_group, storage_account),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group)])

        # enable atp
        self.cmd('security atp update --resource-group {} --storage-account-name {} --is-enabled true'
                 .format(resource_group, storage_account),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('isEnabled', True)])

        # validate atp setting
        self.cmd('security atp show --resource-group {} --storage-account-name {}'
                 .format(resource_group, storage_account),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('isEnabled', True)])

        # disable atp
        self.cmd('security atp update --resource-group {} --storage-account-name {} --is-enabled false'
                 .format(resource_group, storage_account),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('isEnabled', False)])

        # validate atp setting
        self.cmd('security atp show --resource-group {} --storage-account-name {}'
                 .format(resource_group, storage_account),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('isEnabled', False)])
