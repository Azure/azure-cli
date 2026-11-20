# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.core.exceptions import HttpResponseError
from azure.cli.core.azclierror import ResourceNotFoundError
from azure.cli.testsdk import ScenarioTest


class AzureNetAppFilesSmbOplocksScenarioTest(ScenarioTest):
    # Record with: azdev test test_volume_create_with_smb_oplocks --live
    # The active subscription must contain the existing account/pool/network.
    # The account must have working AD configuration reachable from this subnet.
    # Verify oplocks are enabled at creation and can then be disabled.
    # Cleanup attempts deletion of the uniquely named volume even if creation fails.
    def test_volume_create_with_smb_oplocks(self):
        self.kwargs.update({
            'rg': 'sdk-py-test-rg',
            'loc': 'westus2',
            'acc_name': 'shn-ad-smb-na',
            'pool_name': 'cp1',
            'vol_name': self.create_random_name(prefix='cli-smb-', length=24),
            'vnet_name': 'api-test-vnet-westus2stage',
            'subnet_name': 'default',
        })
        pool = self.cmd(
            'az netappfiles pool show -g {rg} -a {acc_name} -p {pool_name}'
        ).get_output_in_json()
        self.kwargs['service_level'] = pool['serviceLevel']
        subnet = self.cmd(
            'az network vnet subnet show -g {rg} --vnet-name {vnet_name} -n {subnet_name}'
        ).get_output_in_json()
        self.kwargs['subnet_id'] = subnet['id']

        checks = [
            self.check('name', '{acc_name}/{pool_name}/{vol_name}'),
            self.check('protocolTypes', ['CIFS']),
            self.check('securityStyle', 'Ntfs'),
            self.check('subnetId', '{subnet_id}'),
        ]
        enabled_checks = checks + [self.check('smbOplocks', 'Enabled')]
        create_attempted = False
        try:
            create_attempted = True
            volume = self.cmd(
                'az netappfiles volume create -g {rg} --account-name {acc_name} --pool-name {pool_name} '
                '--volume-name {vol_name} -l {loc} --creation-token {vol_name} '
                '--service-level {service_level} --usage-threshold 100 --protocol-types CIFS '
                '--smb-oplocks enabled --security-style Ntfs --subnet "{subnet_id}" --vnet {vnet_name}'
            )
            volume.assert_with_checks(enabled_checks)
            self.cmd(
                'az netappfiles volume show -g {rg} -a {acc_name} -p {pool_name} -v {vol_name}',
                checks=enabled_checks,
            )
            disabled_checks = checks + [self.check('smbOplocks', 'Disabled')]
            self.cmd(
                'az netappfiles volume update -g {rg} --account-name {acc_name} --pool-name {pool_name} '
                '--volume-name {vol_name} --smb-oplocks Disabled',
                checks=disabled_checks,
            )
            self.cmd(
                'az netappfiles volume show -g {rg} -a {acc_name} -p {pool_name} -v {vol_name}',
                checks=disabled_checks,
            )
        finally:
            if create_attempted:
                with self.subTest(cleanup='volume'):
                    try:
                        self.cmd(
                            'az netappfiles volume delete -g {rg} -a {acc_name} -p {pool_name} '
                            '-v {vol_name} --force --yes'
                        )
                    except ResourceNotFoundError:
                        pass
                    except HttpResponseError as error:
                        if error.status_code != 404:
                            raise
