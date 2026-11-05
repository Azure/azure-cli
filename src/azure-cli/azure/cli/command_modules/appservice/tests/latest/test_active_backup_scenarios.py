# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os

from azure.cli.testsdk import ScenarioTest
from azure.cli.testsdk.scenario_tests import AllowLargeResponse

from .test_webapp_egress_scenario import EgressRecordingSanitizer


class ActiveBackupScenarioTests(ScenarioTest):
    """Record only against an explicitly approved subscription; replay is offline by default."""

    def __init__(self, method_name):
        super().__init__(method_name, recording_processors=[EgressRecordingSanitizer()])

    def setUp(self):
        if self.in_recording and os.environ.get('AZURE_ACTIVE_BACKUP_LIVE') != '1':
            self.skipTest('Live Active Backup recording requires explicit approval.')
        super().setUp()
        self.kwargs['subscription'] = self.get_subscription_id()
        if self.in_recording:
            expected = os.environ.get('AZURE_ACTIVE_BACKUP_SUBSCRIPTION_ID')
            self.assertTrue(expected, 'Set AZURE_ACTIVE_BACKUP_SUBSCRIPTION_ID to the approved subscription.')
            self.assertEqual(self.kwargs['subscription'].lower(), expected.lower())
        self.plan_silo_created = False
        self.site_silo_created = False

    @AllowLargeResponse(size_kb=8192)
    def test_active_backup_windows_lifecycle(self):
        self._lifecycle(linux=False)

    @AllowLargeResponse(size_kb=8192)
    def test_active_backup_linux_lifecycle(self):
        self._lifecycle(linux=True)

    def _run(self, command, checks=None):
        return self.cmd(command + ' --subscription {subscription}', checks=checks)

    def _lifecycle(self, linux):
        self.kwargs.update(
            rg=self.create_random_name('clitest-ab-', 28),
            plan=self.create_random_name('abplan', 20),
            app=self.create_random_name('abapp', 24),
            vnet=self.create_random_name('abvnet', 20),
            plan_silo='backupplan',
            site_silo='backupapp',
            primary=os.environ.get('AZURE_ACTIVE_BACKUP_PRIMARY_LOCATION', 'eastasia'),
            secondary=os.environ.get('AZURE_ACTIVE_BACKUP_SECONDARY_LOCATION', 'westcentralus'),
            linux='true' if linux else 'false',
        )
        self._run('group create -n {rg} -l {primary} --tags purpose=azure-cli-active-backup-test')
        self.addCleanup(self._delete_group)
        self._run('appservice plan create -g {rg} -n {plan} --location {primary} '
                  '--sku P1V3 --number-of-workers 2 --is-linux {linux}')
        self._run('webapp create -g {rg} -n {app} --plan {plan}' +
                  (' --runtime "PYTHON:3.12"' if linux else ''))

        self._run('appservice plan silo create -g {rg} -n {plan} --silo {plan_silo} '
                  '--location {secondary} --primary-location {primary} --number-of-workers 2 --no-wait')
        self.plan_silo_created = True
        self.addCleanup(self._delete_plan_silo)
        self._run('appservice plan silo wait -g {rg} -n {plan} --silo {plan_silo} '
                  '--created --interval 10 --timeout 1800')
        self._run('appservice plan silo show -g {rg} -n {plan} --silo {plan_silo}', checks=[
            self.check('location', '{secondary}'),
            self.check('properties.provisioningState', 'Succeeded'),
        ])
        self._run('appservice plan silo list -g {rg} -n {plan}', checks=[
            self.check("[?name=='{plan_silo}'] | length(@)", 1),
        ])
        self._run('appservice plan silo update -g {rg} -n {plan} --silo {plan_silo} '
                  '--number-of-workers 2 --no-wait')
        self._run('appservice plan silo wait -g {rg} -n {plan} --silo {plan_silo} '
                  '--updated --interval 10 --timeout 1800')

        self._run('webapp silo create -g {rg} -n {app} --silo {site_silo} --location {secondary} '
                  '--primary-location {primary} --traffic-mode Active --no-wait')
        self.site_silo_created = True
        self.addCleanup(self._delete_site_silo)
        self._run('webapp silo wait -g {rg} -n {app} --silo {site_silo} '
                  '--created --interval 10 --timeout 1800')
        self._run('webapp silo show -g {rg} -n {app} --silo {site_silo}', checks=[
            self.check('location', '{secondary}'),
            self.check('properties.provisioningState', 'Succeeded'),
        ])
        self._run('webapp silo list -g {rg} -n {app}', checks=[
            self.check("[?name=='{site_silo}'] | length(@)", 1),
        ])
        self._run('webapp silo update -g {rg} -n {app} --silo {site_silo} '
                  '--follow-last-known-good false --no-wait')
        self._run('webapp silo wait -g {rg} -n {app} --silo {site_silo} '
                  '--updated --interval 10 --timeout 1800')
        self._run('webapp silo show -g {rg} -n {app} --silo {site_silo}', checks=[
            self.check('properties.followLastKnownGood', False),
        ])

        self._run('network vnet create -g {rg} -n {vnet} -l {secondary} '
                  '--address-prefixes 10.237.16.0/24 --subnet-name integration --subnet-prefixes 10.237.16.0/26')
        subnet = self._run(
            'network vnet subnet update -g {rg} --vnet-name {vnet} -n integration '
            '--delegations Microsoft.Web/serverFarms').get_output_in_json()
        self.kwargs['subnet'] = subnet['id']
        self._run('webapp silo vnet-integration add -g {rg} -n {app} --silo {site_silo} --subnet {subnet}')
        self._run('webapp silo vnet-integration show -g {rg} -n {app} --silo {site_silo}', checks=[
            self.check('subnetResourceId', '{subnet}'),
        ])
        self._run('webapp silo vnet-integration update -g {rg} -n {app} --silo {site_silo} --subnet {subnet}')
        self._run('appservice plan silo vnet-integration list -g {rg} -n {plan} --silo {plan_silo}')
        self._run('webapp silo vnet-integration remove -g {rg} -n {app} --silo {site_silo} --yes')

        self._run('webapp managed-traffic update -g {rg} -n {app} --traffic-mode Passive')
        self._run('webapp managed-traffic show -g {rg} -n {app}')
        self._run('webapp managed-traffic list -g {rg} -n {app} --expand endpoints')
        self._run('webapp last-known-good mark -g {rg} -n {app}')
        self._run('webapp last-known-good show -g {rg} -n {app}')
        self._run('webapp last-known-good list -g {rg} -n {app}')
        self._run('webapp silo refresh -g {rg} -n {app}')

        self._delete_site_silo()
        self._delete_plan_silo()

    def _delete_site_silo(self):
        if self.site_silo_created:
            self._run('webapp silo delete -g {rg} -n {app} --silo {site_silo} --yes --no-wait')
            self._run('webapp silo wait -g {rg} -n {app} --silo {site_silo} '
                      '--deleted --interval 10 --timeout 1800')
            self.site_silo_created = False

    def _delete_plan_silo(self):
        if self.plan_silo_created:
            self._run('appservice plan silo delete -g {rg} -n {plan} --silo {plan_silo} --yes --no-wait')
            self._run('appservice plan silo wait -g {rg} -n {plan} --silo {plan_silo} '
                      '--deleted --interval 10 --timeout 1800')
            self.plan_silo_created = False

    def _delete_group(self):
        self._run('group delete -n {rg} --yes')
        self._run('group exists -n {rg}', checks=[self.check('@', False)])
