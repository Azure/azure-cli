# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
# pylint: disable=too-few-public-methods

import json
import unittest
import jmespath
from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.core.azclierror import (ResourceNotFoundError, ArgumentUsageError, InvalidArgumentValueError,
                                       MutuallyExclusiveArgumentError)
from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, JMESPathCheck)
from knack.cli import CLIError
from knack.log import get_logger

logger = get_logger(__name__)

WINDOWS_ASP_LOCATION_WEBAPP = 'japanwest'
WINDOWS_ASP_LOCATION_FUNCTIONAPP = 'francecentral'
LINUX_ASP_LOCATION_WEBAPP = 'eastus2'
LINUX_ASP_LOCATION_FUNCTIONAPP = 'ukwest'


class WebAppAccessRestrictionScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_WEBAPP)
    def test_webapp_access_restriction_show(self, resource_group):
        self.kwargs.update({
            'app_name': self.create_random_name(prefix='cli-webapp-nwr', length=24),
            'plan_name': self.create_random_name(prefix='cli-plan-nwr', length=24)
        })

        self.cmd('appservice plan create -g {rg} -n {plan_name}')
        self.cmd('webapp create -g {rg} -n {app_name} --plan {plan_name}', checks=[
            JMESPathCheck('state', 'Running')
        ])

        self.cmd('webapp config access-restriction show -g {rg} -n {app_name}', checks=[
            JMESPathCheck('length(@)', 3),
            JMESPathCheck('length(ipSecurityRestrictions)', 1),
            JMESPathCheck('ipSecurityRestrictions[0].name', 'Allow all'),
            JMESPathCheck('ipSecurityRestrictions[0].action', 'Allow'),
            JMESPathCheck('length(scmIpSecurityRestrictions)', 1),
            JMESPathCheck('scmIpSecurityRestrictions[0].name', 'Allow all'),
            JMESPathCheck('scmIpSecurityRestrictions[0].action', 'Allow'),
            JMESPathCheck('scmIpSecurityRestrictionsUseMain', False)
        ])

    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_WEBAPP)
    def test_webapp_access_restriction_set_simple(self, resource_group):
        self.kwargs.update({
            'app_name': self.create_random_name(prefix='cli-webapp-nwr', length=24),
            'plan_name': self.create_random_name(prefix='cli-plan-nwr', length=24)
        })

        self.cmd('appservice plan create -g {rg} -n {plan_name}')
        self.cmd('webapp create -g {rg} -n {app_name} --plan {plan_name}', checks=[
            JMESPathCheck('state', 'Running')
        ])

        self.cmd('webapp config access-restriction set -g {rg} -n {app_name} --use-same-restrictions-for-scm-site true', checks=[
            JMESPathCheck('scmIpSecurityRestrictionsUseMain', True)
        ])

    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_WEBAPP)
    def test_webapp_access_restriction_set_complex(self, resource_group):
        self.kwargs.update({
            'app_name': self.create_random_name(prefix='cli-webapp-nwr', length=24),
            'plan_name': self.create_random_name(prefix='cli-plan-nwr', length=24)
        })

        self.cmd('appservice plan create -g {rg} -n {plan_name}')
        self.cmd('webapp create -g {rg} -n {app_name} --plan {plan_name}', checks=[
            JMESPathCheck('state', 'Running')
        ])

        self.cmd('webapp config access-restriction set -g {rg} -n {app_name} --use-same-restrictions-for-scm-site', checks=[
            JMESPathCheck('scmIpSecurityRestrictionsUseMain', True)
        ])

        self.cmd('webapp config access-restriction set -g {rg} -n {app_name} --use-same-restrictions-for-scm-site false', checks=[
            JMESPathCheck('scmIpSecurityRestrictionsUseMain', False)
        ])

    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_WEBAPP)
    def test_webapp_access_restriction_add(self, resource_group):
        self.kwargs.update({
            'app_name': self.create_random_name(prefix='cli-webapp-nwr', length=24),
            'plan_name': self.create_random_name(prefix='cli-plan-nwr', length=24)
        })

        self.cmd('appservice plan create -g {rg} -n {plan_name}')
        self.cmd('webapp create -g {rg} -n {app_name} --plan {plan_name}', checks=[
            JMESPathCheck('state', 'Running')
        ])

        self.cmd('webapp config access-restriction add -g {rg} -n {app_name} --rule-name developers --action Allow --ip-address 130.220.0.0/27 --priority 200', checks=[
            JMESPathCheck('length(@)', 2),
            JMESPathCheck('[0].name', 'developers'),
            JMESPathCheck('[0].action', 'Allow'),
            JMESPathCheck('[1].name', 'Deny all'),
            JMESPathCheck('[1].action', 'Deny')
        ])

    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_WEBAPP)
    def test_webapp_access_restriction_add_ip_address_validation(self, resource_group):
        self.kwargs.update({
            'app_name': self.create_random_name(prefix='cli-webapp-nwr', length=24),
            'plan_name': self.create_random_name(prefix='cli-plan-nwr', length=24)
        })

        self.cmd('appservice plan create -g {rg} -n {plan_name}')
        self.cmd('webapp create -g {rg} -n {app_name} --plan {plan_name}', checks=[
            JMESPathCheck('state', 'Running')
        ])

        self.cmd('webapp config access-restriction add -g {rg} -n {app_name} --rule-name ipv4 --action Allow --ip-address 130.220.0.0 --priority 200', checks=[
            JMESPathCheck('length(@)', 2),
            JMESPathCheck('[0].name', 'ipv4'),
            JMESPathCheck('[0].action', 'Allow'),
            JMESPathCheck('[0].ipAddress', '130.220.0.0/32'),
            JMESPathCheck('[1].name', 'Deny all'),
            JMESPathCheck('[1].action', 'Deny')
        ])

        self.cmd('webapp config access-restriction add -g {rg} -n {app_name} --rule-name ipv6 --action Allow --ip-address 2004::1000 --priority 200', checks=[
            JMESPathCheck('length(@)', 3),
            JMESPathCheck('[1].name', 'ipv6'),
            JMESPathCheck('[1].action', 'Allow'),
            JMESPathCheck('[1].ipAddress', '2004::1000/128')
        ])

        self.cmd('webapp config access-restriction add -g {rg} -n {app_name} --rule-name multi-source --action Allow --ip-address "2004::1000/120,192.168.0.0/24" --priority 200', checks=[
            JMESPathCheck('length(@)', 4),
            JMESPathCheck('[2].name', 'multi-source'),
            JMESPathCheck('[2].action', 'Allow'),
            JMESPathCheck('[2].ipAddress', '2004::1000/120,192.168.0.0/24')
        ])

    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_WEBAPP)
    def test_webapp_access_restriction_add_service_tag_validation(self, resource_group):
        self.kwargs.update({
            'app_name': self.create_random_name(prefix='cli-webapp-nwr', length=24),
            'plan_name': self.create_random_name(prefix='cli-plan-nwr', length=24)
        })

        self.cmd('appservice plan create -g {rg} -n {plan_name}')
        self.cmd('webapp create -g {rg} -n {app_name} --plan {plan_name}', checks=[
            JMESPathCheck('state', 'Running')
        ])

        self.cmd('webapp config access-restriction add -g {rg} -n {app_name} --rule-name afd --action Allow --service-tag AzureFrontDoor.Backend --priority 200', checks=[
            JMESPathCheck('length(@)', 2),
            JMESPathCheck('[0].name', 'afd'),
            JMESPathCheck('[0].action', 'Allow'),
            JMESPathCheck('[0].ipAddress', 'AzureFrontDoor.Backend'),
            JMESPathCheck('[0].tag', 'ServiceTag'),
            JMESPathCheck('[1].name', 'Deny all'),
            JMESPathCheck('[1].action', 'Deny')
        ])

        self.cmd('webapp config access-restriction add -g {rg} -n {app_name} --rule-name europe --action Allow --service-tag "AzureCloud.WestEurope,AzureCloud.NorthEurope" --priority 300', checks=[
            JMESPathCheck('length(@)', 3),
            JMESPathCheck('[1].name', 'europe'),
            JMESPathCheck('[1].action', 'Allow'),
            JMESPathCheck('[1].ipAddress', 'AzureCloud.WestEurope,AzureCloud.NorthEurope')
        ])

    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(location=LINUX_ASP_LOCATION_WEBAPP)
    def test_webapp_access_restriction_add_http_header(self, resource_group):
        self.kwargs.update({
            'app_name': self.create_random_name(prefix='cli-webapp-nwr', length=24),
            'plan_name': self.create_random_name(prefix='cli-plan-nwr', length=24)
        })

        self.cmd('appservice plan create -g {rg} -n {plan_name} --is-linux')
        self.cmd('webapp create -g {rg} -n {app_name} --plan {plan_name} --runtime "DOTNETCORE|3.1"', checks=[
            JMESPathCheck('state', 'Running')
        ])

        self.cmd('webapp config access-restriction add -g {rg} -n {app_name} --rule-name afd --action Allow --service-tag AzureFrontDoor.Backend --priority 200 --http-header x-azure-fdid=12345678-abcd-1234-abcd-12345678910a', checks=[
            JMESPathCheck('length(@)', 2),
            JMESPathCheck('[0].name', 'afd'),
            JMESPathCheck('[0].action', 'Allow'),
            JMESPathCheck('[0].ipAddress', 'AzureFrontDoor.Backend'),
            JMESPathCheck('[0].tag', 'ServiceTag'),
            JMESPathCheck('length([0].headers)', 1),
            JMESPathCheck('[1].name', 'Deny all'),
            JMESPathCheck('[1].action', 'Deny')
        ])

        self.cmd('webapp config access-restriction remove -g {rg} -n {app_name} --service-tag AzureFrontDoor.Backend', checks=[
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].name', 'Allow all'),
            JMESPathCheck('[0].action', 'Allow')
        ])

        self.cmd('webapp config access-restriction add -g {rg} -n {app_name} --rule-name afd-extended --action Allow --service-tag AzureFrontDoor.Backend --priority 200 --http-header x-azure-fdid=12345678-abcd-1234-abcd-12345678910a x-azure-FDID=next-id x-forwarded-host=contoso.com', checks=[
            JMESPathCheck('length(@)', 2),
            JMESPathCheck('[0].name', 'afd-extended'),
            JMESPathCheck('[0].action', 'Allow'),
            JMESPathCheck('[0].ipAddress', 'AzureFrontDoor.Backend'),
            JMESPathCheck('[0].tag', 'ServiceTag'),
            JMESPathCheck('length([0].headers)', 2),
            JMESPathCheck('length([0].headers.\"x-azure-fdid\")', 2),
            JMESPathCheck('length([0].headers.\"x-forwarded-host\")', 1)
        ])

    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_WEBAPP)
    def test_webapp_access_restriction_add_service_endpoint(self, resource_group):
        self.kwargs.update({
            'app_name': self.create_random_name(prefix='cli-webapp-nwr', length=24),
            'plan_name': self.create_random_name(prefix='cli-plan-nwr', length=24),
            'vnet_name': self.create_random_name(prefix='cli-vnet-nwr', length=24)
        })

        self.cmd('appservice plan create -g {rg} -n {plan_name}')
        self.cmd('webapp create -g {rg} -n {app_name} --plan {plan_name}', checks=[
            JMESPathCheck('state', 'Running')
        ])

        self.cmd('az network vnet create -g {rg} -n {vnet_name} --address-prefixes 10.0.0.0/16 --subnet-name endpoint-subnet --subnet-prefixes 10.0.0.0/24', checks=[
            JMESPathCheck('subnets[0].serviceEndpoints', None)
        ])

        self.cmd('webapp config access-restriction add -g {rg} -n {app_name} --rule-name vnet-integration --action Allow --vnet-name {vnet_name} --subnet endpoint-subnet --priority 150', checks=[
            JMESPathCheck('length(@)', 2),
            JMESPathCheck('[0].name', 'vnet-integration'),
            JMESPathCheck('[0].action', 'Allow'),
            JMESPathCheck('[1].name', 'Deny all'),
            JMESPathCheck('[1].action', 'Deny')
        ])

    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_WEBAPP)
    def test_webapp_access_restriction_remove(self, resource_group):
        self.kwargs.update({
            'app_name': self.create_random_name(prefix='cli-webapp-nwr', length=24),
            'plan_name': self.create_random_name(prefix='cli-plan-nwr', length=24)
        })

        self.cmd('appservice plan create -g {rg} -n {plan_name}')
        self.cmd('webapp create -g {rg} -n {app_name} --plan {plan_name}', checks=[
            JMESPathCheck('state', 'Running')
        ])

        self.cmd('webapp config access-restriction add -g {rg} -n {app_name} --rule-name developers --action Allow --ip-address 130.220.0.0/27 --priority 200', checks=[
            JMESPathCheck('length(@)', 2),
            JMESPathCheck('[0].name', 'developers'),
            JMESPathCheck('[0].action', 'Allow'),
            JMESPathCheck('[1].name', 'Deny all'),
            JMESPathCheck('[1].action', 'Deny')
        ])

        self.cmd('webapp config access-restriction remove -g {rg} -n {app_name} --rule-name developers', checks=[
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].name', 'Allow all'),
            JMESPathCheck('[0].action', 'Allow')
        ])

    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_WEBAPP)
    def test_webapp_access_restriction_mixed_remove(self, resource_group):
        self.kwargs.update({
            'app_name': self.create_random_name(prefix='cli-webapp-nwr', length=24),
            'plan_name': self.create_random_name(prefix='cli-plan-nwr', length=24),
            'vnet_name': self.create_random_name(prefix='cli-vnet-nwr', length=24),
            'ip_address': '130.220.0.0/27',
            'service_tag': 'AzureFrontDoor.Backend'
        })

        self.cmd('appservice plan create -g {rg} -n {plan_name}')
        self.cmd('webapp create -g {rg} -n {app_name} --plan {plan_name}', checks=[
            JMESPathCheck('state', 'Running')
        ])

        self.cmd('az network vnet create -g {rg} -n {vnet_name} --address-prefixes 10.0.0.0/16 --subnet-name endpoint-subnet --subnet-prefixes 10.0.0.0/24', checks=[
            JMESPathCheck('subnets[0].serviceEndpoints', None)
        ])

        self.cmd('webapp config access-restriction add -g {rg} -n {app_name} --rule-name developers --action Allow --ip-address {ip_address} --priority 100', checks=[
            JMESPathCheck('length(@)', 2),
            JMESPathCheck('[0].name', 'developers'),
            JMESPathCheck('[0].action', 'Allow'),
            JMESPathCheck('[1].name', 'Deny all'),
            JMESPathCheck('[1].action', 'Deny')
        ])

        self.cmd('webapp config access-restriction add -g {rg} -n {app_name} --rule-name vnet-integration --action Allow --vnet-name {vnet_name} --subnet endpoint-subnet --priority 150', checks=[
            JMESPathCheck('length(@)', 3),
            JMESPathCheck('[1].name', 'vnet-integration'),
            JMESPathCheck('[1].action', 'Allow'),
            JMESPathCheck('[2].name', 'Deny all'),
            JMESPathCheck('[2].action', 'Deny')
        ])

        self.cmd('webapp config access-restriction add -g {rg} -n {app_name} --rule-name afd --action Allow --service-tag {service_tag} --priority 200 --http-header x-azure-fdid=12345678-abcd-1234-abcd-12345678910a', checks=[
            JMESPathCheck('length(@)', 4),
            JMESPathCheck('[2].name', 'afd'),
            JMESPathCheck('[2].action', 'Allow'),
            JMESPathCheck('[2].ipAddress', 'AzureFrontDoor.Backend'),
            JMESPathCheck('[2].tag', 'ServiceTag'),
            JMESPathCheck('length([2].headers)', 1),
            JMESPathCheck('[3].name', 'Deny all'),
            JMESPathCheck('[3].action', 'Deny')
        ])

        self.cmd('webapp config access-restriction remove -g {rg} -n {app_name} --vnet-name {vnet_name} --subnet endpoint-subnet', checks=[
            JMESPathCheck('length(@)', 3)
        ])

        self.cmd('webapp config access-restriction remove -g {rg} -n {app_name} --ip-address {ip_address}', checks=[
            JMESPathCheck('length(@)', 2)
        ])

        self.cmd('webapp config access-restriction remove -g {rg} -n {app_name} --service-tag {service_tag}', checks=[
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].name', 'Allow all'),
            JMESPathCheck('[0].action', 'Allow')
        ])

    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_WEBAPP)
    def test_webapp_access_restriction_add_scm(self, resource_group):
        self.kwargs.update({
            'app_name': self.create_random_name(prefix='cli-webapp-nwr', length=24),
            'plan_name': self.create_random_name(prefix='cli-plan-nwr', length=24)
        })

        self.cmd('appservice plan create -g {rg} -n {plan_name}')
        self.cmd('webapp create -g {rg} -n {app_name} --plan {plan_name}', checks=[
            JMESPathCheck('state', 'Running')
        ])

        self.cmd('webapp config access-restriction add -g {rg} -n {app_name} --rule-name developers --action Allow --ip-address 130.220.0.0/27 --priority 200 --scm-site', checks=[
            JMESPathCheck('length(@)', 2),
            JMESPathCheck('[0].name', 'developers'),
            JMESPathCheck('[0].action', 'Allow'),
            JMESPathCheck('[1].name', 'Deny all'),
            JMESPathCheck('[1].action', 'Deny')
        ])

    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_WEBAPP)
    def test_webapp_access_restriction_remove_scm(self, resource_group):
        self.kwargs.update({
            'app_name': self.create_random_name(prefix='cli-webapp-nwr', length=24),
            'plan_name': self.create_random_name(prefix='cli-plan-nwr', length=24)
        })

        self.cmd('appservice plan create -g {rg} -n {plan_name}')
        self.cmd('webapp create -g {rg} -n {app_name} --plan {plan_name}', checks=[
            JMESPathCheck('state', 'Running')
        ])

        self.cmd('webapp config access-restriction add -g {rg} -n {app_name} --rule-name developers --action Allow --ip-address 130.220.0.0/27 --priority 200 --scm-site', checks=[
            JMESPathCheck('length(@)', 2),
            JMESPathCheck('[0].name', 'developers'),
            JMESPathCheck('[0].action', 'Allow'),
            JMESPathCheck('[1].name', 'Deny all'),
            JMESPathCheck('[1].action', 'Deny')
        ])

        self.cmd('webapp config access-restriction remove -g {rg} -n {app_name} --rule-name developers --scm-site', checks=[
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].name', 'Allow all'),
            JMESPathCheck('[0].action', 'Allow')
        ])

    @ResourceGroupPreparer(location=WINDOWS_ASP_LOCATION_WEBAPP)
    def test_webapp_access_restriction_slot(self, resource_group):
        self.kwargs.update({
            'app_name': self.create_random_name(prefix='cli-webapp-nwr', length=24),
            'plan_name': self.create_random_name(prefix='cli-plan-nwr', length=24),
            'slot_name': 'stage'
        })

        self.cmd('appservice plan create -g {rg} -n {plan_name} --sku S1')
        self.cmd('webapp create -g {rg} -n {app_name} --plan {plan_name}', checks=[
            JMESPathCheck('state', 'Running')
        ])
        self.cmd('webapp deployment slot create -g {rg} -n {app_name} --slot {slot_name}', checks=[
            JMESPathCheck('state', 'Running')
        ])

        self.cmd('webapp config access-restriction show -g {rg} -n {app_name} --slot {slot_name}', checks=[
            JMESPathCheck('length(@)', 3),
            JMESPathCheck('length(ipSecurityRestrictions)', 1),
            JMESPathCheck('ipSecurityRestrictions[0].name', 'Allow all'),
            JMESPathCheck('ipSecurityRestrictions[0].action', 'Allow'),
            JMESPathCheck('length(scmIpSecurityRestrictions)', 1),
            JMESPathCheck('scmIpSecurityRestrictions[0].name', 'Allow all'),
            JMESPathCheck('scmIpSecurityRestrictions[0].action', 'Allow'),
            JMESPathCheck('scmIpSecurityRestrictionsUseMain', False)
        ])

        self.cmd('webapp config access-restriction add -g {rg} -n {app_name} --rule-name developers --action Allow --ip-address 130.220.0.0/27 --priority 200 --slot {slot_name}', checks=[
            JMESPathCheck('length(@)', 2),
            JMESPathCheck('[0].name', 'developers'),
            JMESPathCheck('[0].action', 'Allow'),
            JMESPathCheck('[1].name', 'Deny all'),
            JMESPathCheck('[1].action', 'Deny')
        ])


if __name__ == '__main__':
    unittest.main()
