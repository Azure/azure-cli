# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import unittest

from azure_devtools.scenario_tests import AllowLargeResponse
from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer)


TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))


class ApimScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_apim-', parameter_name_for_location='resource_group_location')
    def test_apim_core_service(self, resource_group, resource_group_location):
        service_name = self.create_random_name('cli-test-apim-', 50)

        #try to use the injected location, but if the location is not known
        #fall back to west us, otherwise we can't validate since the sdk returns displayName
        if not resource_group_location in KNOWN_LOCS.keys():
            resource_group_location = 'westus'

        self.kwargs.update({
            'service_name': service_name,
            'rg_loc': resource_group_location,
            'rg_loc_displayName': KNOWN_LOCS.get(resource_group_location),
            'notification_sender_email': 'notifications@contsoso.com',
            'publisher_email': 'publisher@contsoso.com',
            'publisher_name': 'Contoso',
            'sku_name': 'Developer',
            'skucapacity': 1,
            'enable_cert': True,
            'tags': ["foo=boo"]
        })

        self.cmd('apim check-name -n {service_name}',
                 checks=[self.check('nameAvailable', True)])

        self.cmd('apim create --name {service_name} -g {rg} -l {rg_loc} --sku-name {sku_name} --publisher-email {publisher_email} --publisher-name {publisher_name} --enable-client-certificate {enable_cert}' ,
                 checks=[self.check('name', '{service_name}'),
                         self.check('location', '{rg_loc}'),
                         self.check('sku.name', '{sku_name}'),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('publisherEmail', '{publisher_email}')])

        self.cmd('apim check-name -n {service_name}',
                 checks=[self.check('nameAvailable', False),
                         self.check('reason', 'AlreadyExists')])

        #TODO: add update test, set a tag and then check for it in apim show below

        count = len(self.cmd('apim list').get_output_in_json())

        self.cmd('apim show - {rg} -n {service_name}', checks=[
            self.check('name', '{service_name}'),
            self.check('resourceGroup', '{rg}')
        ])

        self.cmd('apim delete -g {rg} -n {service_name}')
        final_count = len(self.cmd('apim list').get_output_in_json())
        self.assertTrue(final_count, count - 1)

KNOWN_LOCS = {'eastasia': 'EastAsia',
'southeastasia': 'SoutheastAsia',
'centralus': 'CentralUS',
'eastus': 'EastUS',
'eastus2': 'EastUS2',
'westus': 'WestUS',
'northcentralus': 'NorthCentralUS',
'southcentralus': 'SouthCentralUS',
'northeurope': 'NorthEurope',
'westeurope': 'WestEurope',
'japanwest': 'JapanWest',
'japaneast': 'JapanEast',
'brazilsouth': 'BrazilSouth',
'australiaeast': 'AustraliaEast',
'australiasoutheast': 'AustraliaSoutheast',
'southindia': 'SouthIndia',
'centralindia': 'CentralIndia',
'westindia': 'WestIndia',
'canadacentral': 'CanadaCentral',
'canadaeast': 'CanadaEast',
'uksouth': 'UKSouth',
'ukwest': 'UKWest',
'westcentralus': 'WestCentralUS',
'westus2': 'WestUS2',
'koreacentral': 'KoreaCentral',
'koreasouth': 'KoreaSouth',
'francecentral': 'FranceCentral',
'francesouth': 'FranceSouth',
'australiacentral': 'AustraliaCentral',
'australiacentral2': 'AustraliaCentral2',
'uaecentral': 'UAECentral',
'uaenorth': 'UAENorth',
'southafricanorth': 'SouthAfricaNorth',
'southafricawest': 'SouthAfricaWest'}