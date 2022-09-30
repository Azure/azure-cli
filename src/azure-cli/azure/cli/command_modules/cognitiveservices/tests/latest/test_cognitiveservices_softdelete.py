# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import os
import time
import unittest

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer
from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from knack.util import CLIError


class CognitiveServicesTests(ScenarioTest):
    @ResourceGroupPreparer()
    def test_cognitiveservices_softdelete(self, resource_group):
        sname = self.create_random_name(prefix='cs_cli_test_', length=16)
        customdomain = self.create_random_name(prefix='csclitest', length=16)

        self.kwargs.update({
            'sname': sname,
            'kind': 'FormRecognizer',
            'sku': 'S0',
            'location': 'centraluseuap',
            'customdomain': customdomain
        })

        # test to create cognitive services account
        self.cmd('az cognitiveservices account create -n {sname} -g {rg} --kind {kind} --sku {sku} -l {location} --custom-domain {customdomain} --yes',
                 checks=[self.check('name', '{sname}'),
                         self.check('location', '{location}'),
                         self.check('sku.name', '{sku}'),
                         self.check('properties.customSubDomainName', '{customdomain}')])

        # test to show the details of cognitive services account
        self.cmd('az cognitiveservices account show -n {sname} -g {rg}',
                 checks=[self.check('name', '{sname}'),
                         self.check('resourceGroup', '{rg}'),
                         self.check('properties.customSubDomainName', '{customdomain}')])

        # test to update the properties of cognitive services account
        self.cmd('az cognitiveservices account delete -n {sname} -g {rg}')

        self.cmd('az cognitiveservices account show-deleted --location {location} -n {sname} -g {rg}',
                 checks=[self.check('name', '{sname}'),
                         self.check('properties.customSubDomainName', '{customdomain}')])

        self.cmd('az cognitiveservices account recover --location {location} -n {sname} -g {rg}')

        self.cmd('az cognitiveservices account show -n {sname} -g {rg}',
                 checks=[self.check('name', '{sname}'),
                         self.check('resourceGroup', '{rg}'),
                         self.check('properties.customSubDomainName', '{customdomain}')])


        self.cmd('az cognitiveservices account delete -n {sname} -g {rg}')
        self.cmd('az cognitiveservices account purge --location {location} -n {sname} -g {rg}')
        deleted_accounts = self.cmd('az cognitiveservices account list-deleted').get_output_in_json()

        self.assertEqual(0, 0)


if __name__ == '__main__':
    unittest.main()
