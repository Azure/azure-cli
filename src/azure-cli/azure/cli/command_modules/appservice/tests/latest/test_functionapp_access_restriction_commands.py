# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
# pylint: disable=too-few-public-methods

import json
import unittest
import jmespath
from azure.cli.core.azclierror import (ResourceNotFoundError, ArgumentUsageError, InvalidArgumentValueError,
                                       MutuallyExclusiveArgumentError)
from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, JMESPathCheck, StorageAccountPreparer)
from knack.cli import CLIError
from knack.log import get_logger

logger = get_logger(__name__)

WINDOWS_ASP_LOCATION_WEBAPP = 'japanwest'
WINDOWS_ASP_LOCATION_FUNCTIONAPP = 'francecentral'
LINUX_ASP_LOCATION_WEBAPP = 'eastus2'
LINUX_ASP_LOCATION_FUNCTIONAPP = 'ukwest'


class FunctionAppAccessRestrictionScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(parameter_name_for_location='location', location=WINDOWS_ASP_LOCATION_WEBAPP)
    @StorageAccountPreparer()
    def test_functionapp_access_restriction_show(self, resource_group, location):
        self.kwargs.update({
            'app_name': self.create_random_name(prefix='cli-funcapp-nwr', length=24),
            'loc': location
        })

        self.cmd('functionapp create -g {rg} -n {app_name} --consumption-plan-location {loc} -s {sa}', checks=[
            JMESPathCheck('state', 'Running')
        ])

        self.cmd('functionapp config access-restriction show -g {rg} -n {app_name}', checks=[
            JMESPathCheck('length(@)', 3),
            JMESPathCheck('length(ipSecurityRestrictions)', 1),
            JMESPathCheck('ipSecurityRestrictions[0].name', 'Allow all'),
            JMESPathCheck('ipSecurityRestrictions[0].action', 'Allow'),
            JMESPathCheck('length(scmIpSecurityRestrictions)', 1),
            JMESPathCheck('scmIpSecurityRestrictions[0].name', 'Allow all'),
            JMESPathCheck('scmIpSecurityRestrictions[0].action', 'Allow'),
            JMESPathCheck('scmIpSecurityRestrictionsUseMain', False)
        ])

    @ResourceGroupPreparer(parameter_name_for_location='location', location=WINDOWS_ASP_LOCATION_WEBAPP)
    @StorageAccountPreparer()
    def test_functionapp_access_restriction_set_simple(self, resource_group, location):
        self.kwargs.update({
            'app_name': self.create_random_name(prefix='cli-funcapp-nwr', length=24),
            'loc': location
        })

        self.cmd('functionapp create -g {rg} -n {app_name} --consumption-plan-location {loc} -s {sa}', checks=[
            JMESPathCheck('state', 'Running')
        ])

        self.cmd('functionapp config access-restriction set -g {rg} -n {app_name} --use-same-restrictions-for-scm-site true', checks=[
            JMESPathCheck('scmIpSecurityRestrictionsUseMain', True)
        ])

    @ResourceGroupPreparer(parameter_name_for_location='location', location=WINDOWS_ASP_LOCATION_WEBAPP)
    @StorageAccountPreparer()
    def test_functionapp_access_restriction_set_complex(self, resource_group, location):
        self.kwargs.update({
            'app_name': self.create_random_name(prefix='cli-funcapp-nwr', length=24),
            'loc': location
        })

        self.cmd('functionapp create -g {rg} -n {app_name} --consumption-plan-location {loc} -s {sa}', checks=[
            JMESPathCheck('state', 'Running')
        ])

        self.cmd('functionapp config access-restriction set -g {rg} -n {app_name} --use-same-restrictions-for-scm-site', checks=[
            JMESPathCheck('scmIpSecurityRestrictionsUseMain', True)
        ])

        self.cmd('functionapp config access-restriction set -g {rg} -n {app_name} --use-same-restrictions-for-scm-site false', checks=[
            JMESPathCheck('scmIpSecurityRestrictionsUseMain', False)
        ])

    @ResourceGroupPreparer(random_name_length=17, parameter_name_for_location='location', location=WINDOWS_ASP_LOCATION_WEBAPP)
    # random_name_length is temporary until the bug fix in the API is deployed successfully & then should be removed.
    @StorageAccountPreparer()
    def test_functionapp_access_restriction_add(self, resource_group, location):
        self.kwargs.update({
            'app_name': self.create_random_name(prefix='cli-funcapp-nwr', length=24),
            'loc': location
        })

        self.cmd('functionapp create -g {rg} -n {app_name} --consumption-plan-location {loc} -s {sa}', checks=[
            JMESPathCheck('state', 'Running')
        ])

        self.cmd('functionapp config access-restriction add -g {rg} -n {app_name} --rule-name developers --action Allow --ip-address 130.220.0.0/27 --priority 200', checks=[
            JMESPathCheck('length(@)', 2),
            JMESPathCheck('[0].name', 'developers'),
            JMESPathCheck('[0].action', 'Allow'),
            JMESPathCheck('[1].name', 'Deny all'),
            JMESPathCheck('[1].action', 'Deny')
        ])

    @ResourceGroupPreparer(parameter_name_for_location='location', location=WINDOWS_ASP_LOCATION_WEBAPP)
    @StorageAccountPreparer()
    def test_functionapp_access_restriction_add_ip_address_validation(self, resource_group, location):
        self.kwargs.update({
            'app_name': self.create_random_name(prefix='cli-funcapp-nwr', length=24),
            'loc': location
        })

        self.cmd('functionapp create -g {rg} -n {app_name} --consumption-plan-location {loc} -s {sa}', checks=[
            JMESPathCheck('state', 'Running')
        ])

        self.cmd('functionapp config access-restriction add -g {rg} -n {app_name} --rule-name ipv4 --action Allow --ip-address 130.220.0.0 --priority 200', checks=[
            JMESPathCheck('length(@)', 2),
            JMESPathCheck('[0].name', 'ipv4'),
            JMESPathCheck('[0].action', 'Allow'),
            JMESPathCheck('[0].ipAddress', '130.220.0.0/32'),
            JMESPathCheck('[1].name', 'Deny all'),
            JMESPathCheck('[1].action', 'Deny')
        ])

        self.cmd('functionapp config access-restriction add -g {rg} -n {app_name} --rule-name ipv6 --action Allow --ip-address 2004::1000 --priority 200', checks=[
            JMESPathCheck('length(@)', 3),
            JMESPathCheck('[1].name', 'ipv6'),
            JMESPathCheck('[1].action', 'Allow'),
            JMESPathCheck('[1].ipAddress', '2004::1000/128')
        ])

    @ResourceGroupPreparer(parameter_name_for_location='location', location=WINDOWS_ASP_LOCATION_WEBAPP)
    @StorageAccountPreparer()
    def test_functionapp_access_restriction_add_service_endpoint(self, resource_group, location):
        self.kwargs.update({
            'app_name': self.create_random_name(prefix='cli-funcapp-nwr', length=24),
            'plan_name': self.create_random_name(prefix='cli-plan-nwr', length=24),
            'vnet_name': self.create_random_name(prefix='cli-vnet-nwr', length=24)
        })

        self.cmd('appservice plan create -g {rg} -n {plan_name}')
        self.cmd('functionapp create -g {rg} -n {app_name} --plan {plan_name} -s {sa}', checks=[
            JMESPathCheck('state', 'Running')
        ])

        self.cmd('az network vnet create -g {rg} -n {vnet_name} --address-prefixes 10.0.0.0/16 --subnet-name endpoint-subnet --subnet-prefixes 10.0.0.0/24', checks=[
            JMESPathCheck('subnets[0].serviceEndpoints', None)
        ])

        self.cmd('functionapp config access-restriction add -g {rg} -n {app_name} --rule-name vnet-integration --action Allow --vnet-name {vnet_name} --subnet endpoint-subnet --priority 150', checks=[
            JMESPathCheck('length(@)', 2),
            JMESPathCheck('[0].name', 'vnet-integration'),
            JMESPathCheck('[0].action', 'Allow'),
            JMESPathCheck('[1].name', 'Deny all'),
            JMESPathCheck('[1].action', 'Deny')
        ])

    @ResourceGroupPreparer(parameter_name_for_location='location', location=WINDOWS_ASP_LOCATION_WEBAPP)
    @StorageAccountPreparer()
    def test_functionapp_access_restriction_remove(self, resource_group, location):
        self.kwargs.update({
            'app_name': self.create_random_name(prefix='cli-funcapp-nwr', length=24),
            'loc': location
        })

        self.cmd('functionapp create -g {rg} -n {app_name} --consumption-plan-location {loc} -s {sa}', checks=[
            JMESPathCheck('state', 'Running')
        ])

        self.cmd('functionapp config access-restriction add -g {rg} -n {app_name} --rule-name developers --action Allow --ip-address 130.220.0.0/27 --priority 200', checks=[
            JMESPathCheck('length(@)', 2),
            JMESPathCheck('[0].name', 'developers'),
            JMESPathCheck('[0].action', 'Allow'),
            JMESPathCheck('[1].name', 'Deny all'),
            JMESPathCheck('[1].action', 'Deny')
        ])

        self.cmd('functionapp config access-restriction remove -g {rg} -n {app_name} --rule-name developers', checks=[
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].name', 'Allow all'),
            JMESPathCheck('[0].action', 'Allow')
        ])

    @ResourceGroupPreparer(parameter_name_for_location='location', location=WINDOWS_ASP_LOCATION_WEBAPP)
    @StorageAccountPreparer()
    def test_functionapp_access_restriction_add_scm(self, resource_group, location):
        self.kwargs.update({
            'app_name': self.create_random_name(prefix='cli-funcapp-nwr', length=24),
            'loc': location
        })

        self.cmd('functionapp create -g {rg} -n {app_name} --consumption-plan-location {loc} -s {sa}', checks=[
            JMESPathCheck('state', 'Running')
        ])

        self.cmd('functionapp config access-restriction add -g {rg} -n {app_name} --rule-name developers --action Allow --ip-address 130.220.0.0/27 --priority 200 --scm-site', checks=[
            JMESPathCheck('length(@)', 2),
            JMESPathCheck('[0].name', 'developers'),
            JMESPathCheck('[0].action', 'Allow'),
            JMESPathCheck('[1].name', 'Deny all'),
            JMESPathCheck('[1].action', 'Deny')
        ])

    @ResourceGroupPreparer(parameter_name_for_location='location', location=WINDOWS_ASP_LOCATION_WEBAPP)
    @StorageAccountPreparer()
    def test_functionapp_access_restriction_remove_scm(self, resource_group, location):
        self.kwargs.update({
            'app_name': self.create_random_name(prefix='cli-funcapp-nwr', length=24),
            'loc': location
        })

        self.cmd('functionapp create -g {rg} -n {app_name} --consumption-plan-location {loc} -s {sa}', checks=[
            JMESPathCheck('state', 'Running')
        ])

        self.cmd('functionapp config access-restriction add -g {rg} -n {app_name} --rule-name developers --action Allow --ip-address 130.220.0.0/27 --priority 200 --scm-site', checks=[
            JMESPathCheck('length(@)', 2),
            JMESPathCheck('[0].name', 'developers'),
            JMESPathCheck('[0].action', 'Allow'),
            JMESPathCheck('[1].name', 'Deny all'),
            JMESPathCheck('[1].action', 'Deny')
        ])

        self.cmd('functionapp config access-restriction remove -g {rg} -n {app_name} --rule-name developers --scm-site', checks=[
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].name', 'Allow all'),
            JMESPathCheck('[0].action', 'Allow')
        ])

    @unittest.skip("Function app slot shouldn't use webapp")
    @ResourceGroupPreparer(parameter_name_for_location='location', location=WINDOWS_ASP_LOCATION_WEBAPP)
    @StorageAccountPreparer()
    def test_functionapp_access_restriction_slot(self, resource_group, location):
        self.kwargs.update({
            'app_name': self.create_random_name(prefix='cli-funcapp-nwr', length=24),
            'loc': location,
            'slot_name': 'stage'
        })

        self.cmd('functionapp create -g {rg} -n {app_name} --consumption-plan-location {loc} -s {sa}', checks=[
            JMESPathCheck('state', 'Running')
        ])
        self.cmd('functionapp deployment slot create -g {rg} -n {app_name} --slot {slot_name}', checks=[
            JMESPathCheck('state', 'Running')
        ])

        self.cmd('functionapp config access-restriction show -g {rg} -n {app_name} --slot {slot_name}', checks=[
            JMESPathCheck('length(@)', 3),
            JMESPathCheck('length(ipSecurityRestrictions)', 1),
            JMESPathCheck('ipSecurityRestrictions[0].name', 'Allow all'),
            JMESPathCheck('ipSecurityRestrictions[0].action', 'Allow'),
            JMESPathCheck('length(scmIpSecurityRestrictions)', 1),
            JMESPathCheck('scmIpSecurityRestrictions[0].name', 'Allow all'),
            JMESPathCheck('scmIpSecurityRestrictions[0].action', 'Allow'),
            JMESPathCheck('scmIpSecurityRestrictionsUseMain', False)
        ])

        self.cmd('functionapp config access-restriction add -g {rg} -n {app_name} --rule-name developers --action Allow --ip-address 130.220.0.0/27 --priority 200 --slot {slot_name}', checks=[
            JMESPathCheck('length(@)', 2),
            JMESPathCheck('[0].name', 'developers'),
            JMESPathCheck('[0].action', 'Allow'),
            JMESPathCheck('[1].name', 'Deny all'),
            JMESPathCheck('[1].action', 'Deny')
        ])


if __name__ == '__main__':
    unittest.main()
