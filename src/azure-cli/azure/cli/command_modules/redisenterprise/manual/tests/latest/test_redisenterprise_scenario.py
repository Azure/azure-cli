# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

import os
from azure.cli.testsdk import ScenarioTest
from azure.cli.testsdk import ResourceGroupPreparer
from .. import (
    raise_if,
    calc_coverage
)


# Test class for scenario1
class Redisenterprisescenario1Test(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='clitest-redisenterprise-rg1-', key='rg', parameter_name='rg',
                           location='eastus', random_name_length=40)
    def test_redisenterprise_scenario1(self, rg):
        self.kwargs.update({
            'cluster': self.create_random_name(prefix='clitest-cache1-', length=30)
        })
        from ....tests.latest import test_redisenterprise_scenario as g
        g.call_scenario1(self, rg)
        calc_coverage(__file__)
        raise_if()


# Test class for scenario2
class Redisenterprisescenario2Test(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='clitest-redisenterprise-rg2-', key='rg', parameter_name='rg',
                           location='eastus', random_name_length=40)
    def test_redisenterprise_scenario2(self, rg):
        self.kwargs.update({
            'cluster': self.create_random_name(prefix='clitest-cache2-', length=30),
            'no_database': True
        })
        from ....tests.latest import test_redisenterprise_scenario as g
        g.call_scenario2(self, rg)
        calc_coverage(__file__)
        raise_if()
