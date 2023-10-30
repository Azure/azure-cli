# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import unittest
from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer
LOCATION = "westus2"


class AzureNetAppFilesResourceServiceScenarioTest(ScenarioTest):

    #@unittest.skip('(servicefailure) locations/regionInfo is not deployed yet enable when fixed')
    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_resource_regioninfo_', additional_tags={'owner': 'cli_test'})
    def test_get_region_info(self):
        self.kwargs.update({
            'loc': LOCATION,
        })
        
        self.cmd("az netappfiles resource query-region-info -l {loc}", checks=[
            self.check("length(@)", 2)
        ])
