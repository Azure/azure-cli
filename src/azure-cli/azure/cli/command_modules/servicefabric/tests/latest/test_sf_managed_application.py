# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import unittest
from azure.cli.command_modules.servicefabric.tests.latest.test_util import (
    _create_cluster_with_separate_kv,
    _create_managed_cluster,
    _wait_for_managed_cluster_state_ready)
from azure.cli.core.util import CLIError
from azure.cli.testsdk import ScenarioTest, LiveScenarioTest, ResourceGroupPreparer
from azure.cli.core.azclierror import ResourceNotFoundError


class ServiceFabricManagedApplicationTests(ScenarioTest):
    @ResourceGroupPreparer()
    def test_managed_app_type(self):
        self.kwargs.update({
            'cert_tp': '123BDACDCDFB2C7B250192C6078E47D1E1DB119B',
            'loc': 'eastasia',
            'cluster_name': self.create_random_name('sfrp-cli-', 24),
            'vm_password': self.create_random_name('Pass@', 9),
            'app_type_name': 'VotingType',
            'v1': '1.0.0',
            'app_package_v1': 'https://sfmconeboxst.blob.core.windows.net/managed-application-deployment/Voting.sfpkg',
            'v2': '2.0.0',
            'app_package_v2': 'https://sfmconeboxst.blob.core.windows.net/managed-application-deployment/Voting.2.0.0.sfpkg',
            'app_name': self.create_random_name('testApp', 11),
            'stateful_service_type': 'VotingDataType',
            'stateless_service_type': 'VotingWebType',
            'stateful_service_name': self.create_random_name("testSvc", 20),
            'stateless_service_name': self.create_random_name("testSvc2", 20),
            'tags': 'key1=value1 key2=value2',
            'new_tags': 'key2=value3'
        })
        _create_managed_cluster(self, self.kwargs)
        _wait_for_managed_cluster_state_ready(self, self.kwargs)

        # List
        self.cmd('az sf managed-application-type list -g {rg} -c {cluster_name}',
                 checks=[self.is_empty()])
        # Create
        app_type = self.cmd('az sf managed-application-type create -g {rg} -c {cluster_name} --application-type-name {app_type_name} --tags {tags}',
                            checks=[self.check('provisioningState', 'Succeeded')]).get_output_in_json()
        # Show
        self.cmd('az sf managed-application-type show -g {rg} -c {cluster_name} --application-type-name {app_type_name}',
                 checks=[self.check('id', app_type['id']), self.check('tags', app_type['tags'])])
        # Update
        updated_app_type = self.cmd('az sf managed-application-type update -g {rg} -c {cluster_name} --application-type-name {app_type_name} --tags {new_tags}',
                                    checks=[self.check('provisioningState', 'Succeeded')]).get_output_in_json()
        # Show
        self.cmd('az sf managed-application-type show -g {rg} -c {cluster_name} --application-type-name {app_type_name}',
                 checks=[self.check('id', updated_app_type['id']), self.check('tags', updated_app_type['tags'])])
        # Delete
        self.cmd('az sf managed-application-type delete -g {rg} -c {cluster_name} --application-type-name {app_type_name}')

        # SystemExit 3 'not found'
        with self.assertRaisesRegex(SystemExit, '3'):
            self.cmd('az sf managed-application-type show -g {rg} -c {cluster_name} --application-type-name {app_type_name}')

    @ResourceGroupPreparer()
    def test_managed_app_type_version(self):
        self.kwargs.update({
            'cert_tp': '123BDACDCDFB2C7B250192C6078E47D1E1DB119B',
            'loc': 'eastasia',
            'cluster_name': self.create_random_name('sfrp-cli-', 24),
            'vm_password': self.create_random_name('Pass@', 9),
            'app_type_name': 'VotingType',
            'v1': '1.0.0',
            'app_package_v1': 'https://sfmconeboxst.blob.core.windows.net/managed-application-deployment/Voting.sfpkg',
            'v2': '2.0.0',
            'app_package_v2': 'https://sfmconeboxst.blob.core.windows.net/managed-application-deployment/Voting.2.0.0.sfpkg',
            'app_name': self.create_random_name('testApp', 11),
            'stateful_service_type': 'VotingDataType',
            'stateless_service_type': 'VotingWebType',
            'stateful_service_name': self.create_random_name("testSvc", 20),
            'stateless_service_name': self.create_random_name("testSvc2", 20),
            'tags': 'key1=value1 key2=value2',
            'new_tags': 'key2=value3'
        })
        _create_managed_cluster(self, self.kwargs)
        _wait_for_managed_cluster_state_ready(self, self.kwargs)

        # 'not found'
        with self.assertRaisesRegex(Exception, r'\(NotFound\).+not found.'):
            self.cmd('az sf managed-application-type version list -g {rg} -c {cluster_name} --application-type-name {app_type_name}')
        # Create
        app_type_version = self.cmd('az sf managed-application-type version create -g {rg} -c {cluster_name} '
                                    '--application-type-name {app_type_name} --version {v1} --package-url {app_package_v1} --tags {tags}',
                                    checks=[self.check('provisioningState', 'Succeeded')]).get_output_in_json()
        # Show
        self.cmd('az sf managed-application-type version show -g {rg} -c {cluster_name} --application-type-name {app_type_name} --version {v1}',
                 checks=[self.check('id', app_type_version['id']), self.check('tags', app_type_version['tags'])])
        # Update
        updated_app_type_version = self.cmd('az sf managed-application-type version update -g {rg} -c {cluster_name} --application-type-name {app_type_name} --version {v1} --tags {new_tags}',
                                            checks=[self.check('provisioningState', 'Succeeded')]).get_output_in_json()
        # Show
        self.cmd('az sf managed-application-type version show -g {rg} -c {cluster_name} --application-type-name {app_type_name} --version {v1}',
                 checks=[self.check('id', updated_app_type_version['id']), self.check('tags', updated_app_type_version['tags'])])
        # Delete
        self.cmd('az sf managed-application-type version delete -g {rg} -c {cluster_name} --application-type-name {app_type_name} --version {v1}')

        # SystemExit 3 'not found'
        with self.assertRaisesRegex(SystemExit, '3'):
            self.cmd('az sf managed-application-type version show -g {rg} -c {cluster_name} --application-type-name {app_type_name} --version {v1}')

    @ResourceGroupPreparer()
    def test_managed_application(self):
        updated_version = '2.0.0'
        self.kwargs.update({
            'cert_tp': '123BDACDCDFB2C7B250192C6078E47D1E1DB119B',
            'loc': 'eastasia',
            'cluster_name': self.create_random_name('sfrp-cli-', 24),
            'vm_password': self.create_random_name('Pass@', 9),
            'app_type_name': 'VotingType',
            'v1': '1.0.0',
            'app_package_v1': 'https://sfmconeboxst.blob.core.windows.net/managed-application-deployment/Voting.sfpkg',
            'v2': updated_version,
            'app_package_v2': 'https://sfmconeboxst.blob.core.windows.net/managed-application-deployment/Voting.2.0.0.sfpkg',
            'app_name': self.create_random_name('testApp', 11),
            'stateful_service_type': 'VotingDataType',
            'stateless_service_type': 'VotingWebType',
            'stateful_service_name': self.create_random_name("testSvc", 20),
            'stateless_service_name': self.create_random_name("testSvc2", 20),
            'tags': 'key1=value1 key2=value2',
            'new_tags': 'key2=value3'
        })
        _create_managed_cluster(self, self.kwargs)
        _wait_for_managed_cluster_state_ready(self, self.kwargs)

        # List Apps
        self.cmd('az sf managed-application list -g {rg} -c {cluster_name}',
                 checks=[self.is_empty()])
        # Create App
        app = self.cmd('az sf managed-application create -g {rg} -c {cluster_name} --application-name {app_name} '
                       '--application-type-name {app_type_name} --application-type-version {v1} --package-url {app_package_v1}',
                       checks=[self.check('provisioningState', 'Succeeded')]).get_output_in_json()
        # Show App
        self.cmd('az sf managed-application show -g {rg} -c {cluster_name} --application-name {app_name}',
                 checks=[self.check('id', app['id'])])
        # Create Stateless Service
        stateless_service = self.cmd('az sf managed-service create -g {rg} -c {cluster_name} --application-name {app_name} --state stateless --instance-count -1 '
                                     '--service-name {stateless_service_name} --service-type {stateless_service_type} --partition-scheme singleton',
                                     checks=[self.check('properties.provisioningState', 'Succeeded')]).get_output_in_json()
        # Show Stateless Service
        self.cmd('az sf managed-service show -g {rg} -c {cluster_name} --application-name {app_name} --service-name {stateless_service_name}',
                 checks=[self.check('id', stateless_service['id'])])
        # Create New App Type
        self.cmd('az sf managed-application-type version create -g {rg} -c {cluster_name} '
                 '--application-type-name {app_type_name} --version {v2} --package-url {app_package_v2}',
                 checks=[self.check('provisioningState', 'Succeeded')])
        # Update Application
        updated_app = self.cmd('az sf managed-application update -g {rg} -c {cluster_name} --application-name {app_name} --application-type-version {v2} '
                               '--health-check-stable-duration 0 --health-check-wait-duration 0 --health-check-retry-timeout 0 '
                               '--upgrade-domain-timeout 5000 --upgrade-timeout 7000 --failure-action Rollback --upgrade-replica-set-check-timeout 300 --force-restart',
                               checks=[self.check('provisioningState', 'Succeeded'),
                                       self.check('upgradePolicy.forceRestart', True),
                                       self.check('upgradePolicy.upgradeReplicaSetCheckTimeout', '300'),
                                       self.check('upgradePolicy.rollingUpgradeMonitoringPolicy.healthCheckRetryTimeout', '00:00:00'),
                                       self.check('upgradePolicy.rollingUpgradeMonitoringPolicy.healthCheckWaitDuration', '00:00:00'),
                                       self.check('upgradePolicy.rollingUpgradeMonitoringPolicy.healthCheckStableDuration', '00:00:00'),
                                       self.check('upgradePolicy.rollingUpgradeMonitoringPolicy.upgradeTimeout', '01:56:40'),
                                       self.check('upgradePolicy.rollingUpgradeMonitoringPolicy.upgradeDomainTimeout', '01:23:20'),
                                       self.check('upgradePolicy.rollingUpgradeMonitoringPolicy.failureAction', 'Rollback')]).get_output_in_json()
        assert updated_app['version'].endswith(updated_version)
        # Delete Application
        self.cmd('az sf managed-application delete -g {rg} -c {cluster_name} --application-name {app_name}')
        # Delete Application Type
        self.cmd('az sf managed-application-type delete -g {rg} -c {cluster_name} --application-type-name {app_type_name}')

        # SystemExit 3 'not found'
        with self.assertRaisesRegex(SystemExit, '3'):
            self.cmd('az sf managed-application show -g {rg} -c {cluster_name} --application-name {app_name}')

    @ResourceGroupPreparer()
    def test_managed_service(self):
        self.kwargs.update({
            'cert_tp': '123BDACDCDFB2C7B250192C6078E47D1E1DB119B',
            'loc': 'eastasia',
            'cluster_name': self.create_random_name('sfrp-cli-', 24),
            'vm_password': self.create_random_name('Pass@', 9),
            'app_type_name': 'VotingType',
            'v1': '1.0.0',
            'app_package_v1': 'https://sfmconeboxst.blob.core.windows.net/managed-application-deployment/Voting.sfpkg',
            'v2': '2.0.0',
            'app_package_v2': 'https://sfmconeboxst.blob.core.windows.net/managed-application-deployment/Voting.2.0.0.sfpkg',
            'app_name': self.create_random_name('testApp', 11),
            'stateful_service_type': 'VotingDataType',
            'stateless_service_type': 'VotingWebType',
            'stateful_service_name': self.create_random_name("testSvc", 20),
            'stateless_service_name': self.create_random_name("testSvc2", 20),
            'tags': 'key1=value1 key2=value2',
            'new_tags': 'key2=value3',
            'service_placement_time_limit': '00:11:00',
            'standby_replica_keep_duration': '00:11:00',
            'quorum_loss_wait_duration': '00:11:00',
            'replica_restart_wait_duration': '00:11:00',
            'min_instance_count': 2,
            'min_instance_percentage': 20,
        })
        _create_managed_cluster(self, self.kwargs)
        _wait_for_managed_cluster_state_ready(self, self.kwargs)

        # Create App
        self.cmd('az sf managed-application create -g {rg} -c {cluster_name} --application-name {app_name} '
                 '--application-type-name {app_type_name} --application-type-version {v1} --package-url {app_package_v1}',
                 checks=[self.check('provisioningState', 'Succeeded')])
        # List Services
        self.cmd('az sf managed-service list -g {rg} -c {cluster_name} --application-name {app_name}',
                 checks=[self.is_empty()])
        # Create Stateful Service
        stateful_service = self.cmd('az sf managed-service create -g {rg} -c {cluster_name} --application-name {app_name} --state stateful --min-replica-set-size 2 '
                                    '--target-replica-set-size 3 --service-name {stateful_service_name} --service-type {stateful_service_type} --has-persisted-state '
                                    '--partition-scheme uniformint64range --partition-count 1 --low-key 0 --high-key 25',
                                    checks=[self.check('properties.provisioningState', 'Succeeded')]).get_output_in_json()
        # Show Stateful Service
        self.cmd('az sf managed-service show -g {rg} -c {cluster_name} --application-name {app_name} --service-name {stateful_service_name}',
                 checks=[self.check('id', stateful_service['id'])])
        # Create Stateless Service
        stateless_service = self.cmd('az sf managed-service create -g {rg} -c {cluster_name} --application-name {app_name} --state stateless --instance-count -1 '
                                     '--service-name {stateless_service_name} --service-type {stateless_service_type} --partition-scheme singleton',
                                     checks=[self.check('properties.provisioningState', 'Succeeded')]).get_output_in_json()
        # Show Stateless Service
        self.cmd('az sf managed-service show -g {rg} -c {cluster_name} --application-name {app_name} --service-name {stateless_service_name}',
                 checks=[self.check('id', stateless_service['id'])])
        # Update Stateful Service
        self.cmd('az sf managed-service update -g {rg} -c {cluster_name} --application-name {app_name} --service-name {stateful_service_name} '
                 '--service-placement-time-limit {service_placement_time_limit} --stand-by-replica-keep-duration {standby_replica_keep_duration} '
                 '--replica-restart-wait-duration {replica_restart_wait_duration} --quorum-loss-wait-duration {quorum_loss_wait_duration}',
                 checks=[self.check('properties.provisioningState', 'Succeeded'),
                         self.check('properties.servicePlacementTimeLimit', '00:11:00'),
                         self.check('properties.standByReplicaKeepDuration', '00:11:00'),
                         self.check('properties.quorumLossWaitDuration', '00:11:00'),
                         self.check('properties.replicaRestartWaitDuration', '00:11:00')])
        # Update Stateless Service
        self.cmd('az sf managed-service update -g {rg} -c {cluster_name} --application-name {app_name} --service-name {stateless_service_name} '
                 '--min-instance-count {min_instance_count} --min-instance-percentage {min_instance_percentage} ',
                 checks=[self.check('properties.provisioningState', 'Succeeded'),
                         self.check('properties.minInstanceCount', '2'),
                         self.check('properties.minInstancePercentage', '20')])

        # Delete Stateless Service
        self.cmd('az sf managed-service delete -g {rg} -c {cluster_name} --application-name {app_name} --service-name {stateless_service_name}')
        # Delete Stateful Service
        self.cmd('az sf managed-service delete -g {rg} -c {cluster_name} --application-name {app_name} --service-name {stateful_service_name}')
        # Delete Application
        self.cmd('az sf managed-application delete -g {rg} -c {cluster_name} --application-name {app_name}')
        # Delete Application Type
        self.cmd('az sf managed-application-type delete -g {rg} -c {cluster_name} --application-type-name {app_type_name}')

        # SystemExit 3 'not found'
        with self.assertRaisesRegex(SystemExit, '3'):
            self.cmd('az sf managed-service show -g {rg} -c {cluster_name} --application-name {app_name} --service-name {stateful_service_name}')
        # SystemExit 3 'not found'
        with self.assertRaisesRegex(SystemExit, '3'):
            self.cmd('az sf managed-service show -g {rg} -c {cluster_name} --application-name {app_name} --service-name {stateless_service_name}')


if __name__ == '__main__':
    unittest.main()
