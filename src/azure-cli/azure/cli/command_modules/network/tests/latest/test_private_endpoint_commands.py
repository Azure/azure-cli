# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest


from azure.cli.testsdk import (
    ScenarioTest, ResourceGroupPreparer)

from azure.cli.command_modules.keyvault.tests.latest.test_keyvault_commands import _create_keyvault


class NetworkPrivateLinkResourceKeyVaultScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_keyvault_plr')
    def test_private_link_resource_keyvault(self, resource_group):
        self.kwargs.update({
            'kv': self.create_random_name('cli-test-kv-plr-', 24),
            'loc': 'centraluseuap',
            'rg': resource_group
        })

        _create_keyvault(self, self.kwargs)
        self.cmd('network private-link-resource show --name {kv} -g {rg} --resource-provider microsoft.keyvault/vaults',
                 checks=self.check('value[0].groupId', 'vault'))


if __name__ == '__main__':
    unittest.main()
