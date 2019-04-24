# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer)

# pylint: disable=line-too-long
# pylint: disable=too-many-lines

TEST_SSH_KEY_PUB = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQCbIg1guRHbI0lV11wWDt1r2cUdcNd27CJsg+SfgC7miZeubtwUhbsPdhMQsfDyhOWHq1+ZL0M+nJZV63d/1dhmhtgyOqejUwrPlzKhydsbrsdUor+JmNJDdW01v7BXHyuymT8G4s09jCasNOwiufbP/qp72ruu0bIA1nySsvlf9pCQAuFkAnVnf/rFhUlOkhtRpwcq8SUNY2zRHR/EKb/4NWY1JzR4sa3q2fWIJdrrX0DvLoa5g9bIEd4Df79ba7v+yiUBOS0zT2ll+z4g9izHK3EO5d8hL4jYxcjKs+wcslSYRWrascfscLgMlMGh0CdKeNTDjHpGPncaf3Z+FwwwjWeuiNBxv7bJo13/8B/098KlVDl4GZqsoBCEjPyJfV6hO0y/LkRGkk7oHWKgeWAfKtfLItRp00eZ4fcJNK9kCaSMmEugoZWcI7NGbZXzqFWqbpRI7NcDP9+WIQ+i9U5vqWsqd/zng4kbuAJ6UuKqIzB0upYrLShfQE3SAck8oaLhJqqq56VfDuASNpJKidV+zq27HfSBmbXnkR/5AK337dc3MXKJypoK/QPMLKUAP5XLPbs+NddJQV7EZXd29DLgp+fRIg3edpKdO7ZErWhv7d+3Kws+e1Y+ypmR2WIVSwVyBEUfgv2C8Ts9gnTF4pNcEY/S2aBicz5Ew2+jdyGNQQ== test@example.com\n"


class ProximityPlacementGroupScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix="cli_test_ppg_cmds_")
    def test_proximity_placement_group(self, resource_group, resource_group_location):
        self.kwargs.update({
            'ppg1': 'my_ppg_1',
            'ppg2': 'my_ppg_2',
            'loc': resource_group_location
        })

        self.cmd('ppg create -n {ppg1} -t standard -g {rg}', checks=[
            self.check('name', '{ppg1}'),
            self.check('location', '{loc}'),
            self.check('proximityPlacementGroupType', 'Standard')
        ])

        self.cmd('ppg create -n {ppg2} -t ultra -g {rg}', checks=[
            self.check('name', '{ppg2}'),
            self.check('location', '{loc}'),
            self.check('proximityPlacementGroupType', 'Ultra')
        ])

    @ResourceGroupPreparer(name_prefix='cli_test_ppg_resources_')
    def test_ppg_with_related_resources(self, resource_group):
        self.kwargs.update({
            'ppg': 'my_ppg_1',
            'vm': 'vm1',
            'vmss': 'vmss1',
            'avset': 'avset1',
            'ssh_key': TEST_SSH_KEY_PUB
        })

        self.kwargs['ppg_id'] = self.cmd('ppg create -n {ppg} -t standard -g {rg}').get_output_in_json()['id']

        self.kwargs['vm_id'] = self.cmd('vm create -g {rg} -n {vm} --image UbuntuLTS --ssh-key-value \'{ssh_key}\' --ppg {ppg}').get_output_in_json()['id']

        self.cmd('vmss create -g {rg} -n {vmss} --image UbuntuLTS --ssh-key-value \'{ssh_key}\' --ppg {ppg_id}')
        self.kwargs['vmss_id'] = self.cmd('vmss show -g {rg} -n {vmss}').get_output_in_json()['id']

        self.kwargs['avset_id'] = self.cmd('vm availability-set create -g {rg} -n {avset} --ppg {ppg}').get_output_in_json()['id']

        ppg_resource = self.cmd('ppg show -n {ppg} -g {rg}').get_output_in_json()

        # check that the compute resources are created with PPG
        self.assertEqual(ppg_resource['availabilitySets'][0]['id'].lower(), self.kwargs['avset_id'].lower())
        self.assertEqual(ppg_resource['virtualMachines'][0]['id'].lower(), self.kwargs['vm_id'].lower())
        self.assertEqual(ppg_resource['virtualMachineScaleSets'][0]['id'].lower(), self.kwargs['vmss_id'].lower())
