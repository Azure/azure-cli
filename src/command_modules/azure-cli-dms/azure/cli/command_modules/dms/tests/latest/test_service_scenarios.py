# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, JMESPathCheck

class DmsServiceTests(ScenarioTest):
    @ResourceGroupPreparer()
    def test_service_crud(self, resource_group):

        service_name = self.create_random_name("dmsclitest", 20)
        location_name = 'centralus'
        sku_name = 'Basic_2vCores'
        vsubnet_name = '/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/ERNetwork/providers/Microsoft.Network/virtualNetworks/AzureDMS-CORP-USC-VNET-5044/subnets/Subnet-1'

        self.cmd('az dms show -g {} -n {}'.format(resource_group, service_name), expect_failure=True)

        create_checks = [JMESPathCheck('location', location_name),
                         JMESPathCheck('name', service_name),
                         JMESPathCheck('resourceGroup', resource_group),
                         JMESPathCheck('sku.name', sku_name),
                         JMESPathCheck('virtualSubnetId', vsubnet_name),
                         JMESPathCheck('provisioningState', 'Succeeded'),
                         JMESPathCheck('type', 'Microsoft.DataMigration/services')]
        self.cmd('az dms create -l {} -n {} -g {} --sku-name {} --virtual-subnet-id {}'.format(
            location_name,
            service_name,
            resource_group,
            sku_name,
            vsubnet_name), checks=create_checks)

        self.cmd('az dms show -g {} -n {}'.format(resource_group, service_name), checks=create_checks)

        list_checks = [JMESPathCheck('length(@)', 1)]
        self.cmd('az dms list -g {}'.format(resource_group), checks=list_checks)

        status_checks = [JMESPathCheck('status', 'Online'),
                         JMESPathCheck('vmSize', 'Standard_A2_v2')]
        self.cmd('az dms check-status -g {} -n {}'.format(resource_group, service_name), checks=status_checks)

        name_exists_checks = [JMESPathCheck('nameAvailable', False),
                              JMESPathCheck('reason', 'AlreadyExists')]
        self.cmd('az dms check-name-availability -l {} -n {}'.format(location_name, service_name), checks=name_exists_checks)

        self.cmd('az dms delete -g {} -n {}'.format(resource_group, service_name))

        name_available_checks = [JMESPathCheck('nameAvailable', True)]
        self.cmd('az dms check-name-availability -l {} -n {}'.format(location_name, service_name), checks=name_available_checks)
