# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import unittest

from azure.cli.testsdk import LiveScenarioTest, ResourceGroupPreparer


PRIMARY_LOCATION = os.environ.get('AZURE_ACTIVE_BACKUP_PRIMARY_LOCATION', 'eastus')
SILO_LOCATION = os.environ.get('AZURE_ACTIVE_BACKUP_SILO_LOCATION', 'westus2')


@unittest.skipUnless(os.environ.get('AZURE_ACTIVE_BACKUP_LIVE') == '1',
                     'Requires explicit live-resource authorization and an enabled Active Backup subscription.')
class ActiveBackupLiveTests(LiveScenarioTest):

    @ResourceGroupPreparer(location=PRIMARY_LOCATION)
    def test_appservice_active_backup_windows(self, resource_group):
        self._lifecycle(resource_group, linux=False)

    @ResourceGroupPreparer(location=PRIMARY_LOCATION)
    def test_appservice_active_backup_linux(self, resource_group):
        self._lifecycle(resource_group, linux=True)

    def _lifecycle(self, resource_group, linux):
        plan = self.create_random_name('abplan', 20)
        app = self.create_random_name('abapp', 24)
        self.kwargs.update(rg=resource_group, plan=plan, app=app,
                           primary=PRIMARY_LOCATION, secondary=SILO_LOCATION,
                           linux='true' if linux else 'false')
        self.cmd('appservice plan create -g {rg} -n {plan} --location {primary} '
                 '--sku P1V3 --number-of-workers 2 --is-linux {linux}')
        self.cmd('webapp create -g {rg} -n {app} --plan {plan}' +
                 (' --runtime "PYTHON:3.12"' if linux else ''))
        try:
            self.cmd('appservice plan silo create -g {rg} -n {plan} --silo backup-plan '
                     '--location {secondary} --primary-location {primary} --number-of-workers 2')
            self.cmd('webapp silo create -g {rg} -n {app} --silo backup-app --location {secondary} '
                     '--primary-location {primary} --traffic-mode Active')
            self.cmd('webapp silo show -g {rg} -n {app} --silo backup-app',
                     checks=[self.check('properties.provisioningState', 'Succeeded')])
            self.cmd('webapp silo list -g {rg} -n {app}')
            self.cmd('appservice plan silo list -g {rg} -n {plan}')
            self.cmd('appservice plan silo update -g {rg} -n {plan} --silo backup-plan --number-of-workers 2')
            self.cmd('webapp silo update -g {rg} -n {app} --silo backup-app --follow-last-known-good false')
            self.cmd('webapp managed-traffic update -g {rg} -n {app} --traffic-mode Passive')
            self.cmd('webapp managed-traffic list -g {rg} -n {app} --expand-endpoints')
            self.cmd('webapp managed-traffic show -g {rg} -n {app}')
            self.cmd('webapp last-known-good mark -g {rg} -n {app}')
            self.cmd('webapp last-known-good show -g {rg} -n {app}')
            self.cmd('webapp last-known-good list -g {rg} -n {app}')
            self.cmd('webapp silo refresh -g {rg} -n {app}')
            self.cmd('webapp silo config show -g {rg} -n {app} --silo backup-app')
            self.cmd('webapp silo instance list -g {rg} -n {app} --silo backup-app')
            self.cmd('webapp silo deployment list -g {rg} -n {app} --silo backup-app')
            self.cmd('webapp silo restart -g {rg} -n {app} --silo backup-app --synchronous true')
        finally:
            try:
                self.cmd('webapp silo delete -g {rg} -n {app} --silo backup-app --yes')
            finally:
                self.cmd('appservice plan silo delete -g {rg} -n {plan} --silo backup-plan --yes')
