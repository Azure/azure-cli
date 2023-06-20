# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import unittest
from azure.cli.command_modules.servicefabric.tests.latest.test_util import _create_cluster_with_separate_kv
from azure.cli.core.util import CLIError
from azure.cli.testsdk import ScenarioTest, LiveScenarioTest, ResourceGroupPreparer, KeyVaultPreparer


class ServiceFabricApplicationTests(ScenarioTest):
    def _app_type_test(self):
        self.cmd('az sf application-type list -g {rg} -c {cluster_name}',
                 checks=[self.check('length(value)', 0)])
        app_type = self.cmd('az sf application-type create -g {rg} -c {cluster_name} --application-type-name {app_type_name}',
                            checks=[self.check('provisioningState', 'Succeeded')]).get_output_in_json()
        self.cmd('az sf application-type show -g {rg} -c {cluster_name} --application-type-name {app_type_name}',
                 checks=[self.check('id', app_type['id'])])
        self.cmd('az sf application-type delete -g {rg} -c {cluster_name} --application-type-name {app_type_name}')

        # SystemExit 3 'not found'
        with self.assertRaisesRegex(SystemExit, '3'):
            self.cmd('az sf application-type show -g {rg} -c {cluster_name} --application-type-name {app_type_name}')

    def _app_type_version_test(self):
        self.cmd('az sf application-type version list -g {rg} -c {cluster_name} --application-type-name {app_type_name}',
                 checks=[self.check('length(value)', 0)])
        app_type_version = self.cmd('az sf application-type version create -g {rg} -c {cluster_name} '
                                    '--application-type-name {app_type_name} --version {v1} --package-url {app_package_v1}',
                                    checks=[self.check('provisioningState', 'Succeeded')]).get_output_in_json()
        self.cmd('az sf application-type version show -g {rg} -c {cluster_name} --application-type-name {app_type_name} --version {v1}',
                 checks=[self.check('id', app_type_version['id'])])
        self.cmd('az sf application-type version delete -g {rg} -c {cluster_name} --application-type-name {app_type_name} --version {v1}')

        # SystemExit 3 'not found'
        with self.assertRaisesRegex(SystemExit, '3'):
            self.cmd('az sf application-type version show -g {rg} -c {cluster_name} --application-type-name {app_type_name} --version {v1}')

    def _app_service_test(self):
        self.cmd('az sf application list -g {rg} -c {cluster_name}',
                 checks=[self.check('length(value)', 0)])
        app = self.cmd('az sf application create -g {rg} -c {cluster_name} --application-name {app_name} '
                       '--application-type-name {app_type_name} --application-type-version {v1} --package-url {app_package_v1} '
                       '--application-parameters Mode=binary',
                       checks=[self.check('provisioningState', 'Succeeded')]).get_output_in_json()
        self.cmd('az sf application show -g {rg} -c {cluster_name} --application-name {app_name}',
                 checks=[self.check('id', app['id'])])

        service = self.cmd('az sf service create -g {rg} -c {cluster_name} --application-name {app_name} --state stateless --instance-count -1 '
                           '--service-name "{app_name}~testService" --service-type {service_type} --partition-scheme singleton',
                           checks=[self.check('provisioningState', 'Succeeded')]).get_output_in_json()

        self.cmd('az sf service show -g {rg} -c {cluster_name} --application-name {app_name} --service-name "{app_name}~testService"',
                 checks=[self.check('id', service['id'])])

        self.cmd('az sf application-type version create -g {rg} -c {cluster_name} '
                 '--application-type-name {app_type_name} --version {v2} --package-url {app_package_v2}',
                 checks=[self.check('provisioningState', 'Succeeded')])

        self.cmd('az sf application update -g {rg} -c {cluster_name} --application-name {app_name} --application-type-version {v2} '
                 '--application-parameters Precision=3 --health-check-stable-duration 0 --health-check-wait-duration 0 --health-check-retry-timeout 0 '
                 '--upgrade-domain-timeout 5000 --upgrade-timeout 7000 --failure-action Rollback --upgrade-replica-set-check-timeout 300 --force-restart',
                 checks=[self.check('provisioningState', 'Succeeded'),
                         self.check('typeVersion', '{v2}'),
                         self.check('parameters.Mode', 'binary'),
                         self.check('parameters.Precision', '3'),
                         self.check('upgradePolicy.forceRestart', True),
                         self.check('upgradePolicy.upgradeReplicaSetCheckTimeout', '00:05:00'),
                         self.check('upgradePolicy.rollingUpgradeMonitoringPolicy.healthCheckRetryTimeout', '00:00:00'),
                         self.check('upgradePolicy.rollingUpgradeMonitoringPolicy.healthCheckWaitDuration', '00:00:00'),
                         self.check('upgradePolicy.rollingUpgradeMonitoringPolicy.healthCheckStableDuration', '00:00:00'),
                         self.check('upgradePolicy.rollingUpgradeMonitoringPolicy.upgradeTimeout', '01:56:40'),
                         self.check('upgradePolicy.rollingUpgradeMonitoringPolicy.upgradeDomainTimeout', '01:23:20'),
                         self.check('upgradePolicy.rollingUpgradeMonitoringPolicy.failureAction', 'Rollback')])

        self.cmd('az sf application update -g {rg} -c {cluster_name} --application-name {app_name} --minimum-nodes 1 --maximum-nodes 3',
                 checks=[self.check('provisioningState', 'Succeeded')])
        self.cmd('az sf application show -g {rg} -c {cluster_name} --application-name {app_name}',
                 checks=[self.check('provisioningState', 'Succeeded'),
                         self.check('minimumNodes', 1),
                         self.check('maximumNodes', 3)])

        self.cmd('az sf application delete -g {rg} -c {cluster_name} --application-name {app_name}')
        self.cmd('az sf application-type delete -g {rg} -c {cluster_name} --application-type-name {app_type_name}')

        # SystemExit 3 'not found'
        with self.assertRaisesRegex(SystemExit, '3'):
            self.cmd('az sf application show -g {rg} -c {cluster_name} --application-name {app_name}')

    @ResourceGroupPreparer()
    @KeyVaultPreparer(name_prefix='sfrp-cli-kv-', additional_params='--enabled-for-deployment --enabled-for-template-deployment')
    def test_application_related(self, key_vault, resource_group):
        self.kwargs.update({
            'kv_name': key_vault,
            'loc': 'westus',
            'cert_name': self.create_random_name('sfrp-cli-', 24),
            'cluster_name': self.create_random_name('sfrp-cli-', 24),
            'vm_password': self.create_random_name('Pass@', 9),
            'app_type_name': 'CalcServiceApp',
            'v1': '1.0',
            'app_package_v1': 'https://sfrpserviceclienttesting.blob.core.windows.net/test-apps/CalcApp_1.0.sfpkg',
            'v2': '1.2',
            'app_package_v2': 'https://sfrpserviceclienttesting.blob.core.windows.net/test-apps/CalcApp_1.2.sfpkg',
            'app_name': self.create_random_name('testApp', 11),
            'service_type': 'CalcServiceType'
        })

        _create_cluster_with_separate_kv(self, self.kwargs)
        self._app_type_test()
        self._app_type_version_test()
        self._app_service_test()


if __name__ == '__main__':
    unittest.main()
