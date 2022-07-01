# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# AZURE CLI EventHub - NAMESPACE TEST DEFINITIONS

import time

from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, KeyVaultPreparer)


# pylint: disable=line-too-long
# pylint: disable=too-many-lines


class EHNamespaceAppl(ScenarioTest):
    from azure.cli.testsdk.scenario_tests import AllowLargeResponse

    @AllowLargeResponse()
    @ResourceGroupPreparer(name_prefix='cli_test_eh_namespace')
    def test_eventhub_app_group(self, resource_group):
        self.kwargs.update({
            'loc': 'westus2',
            'rg': resource_group,
            'namespacename': self.create_random_name(prefix='eventhubs-nscli', length=20),
            'appgroup1': self.create_random_name(prefix='app-group-nscli1', length=20),
            'appgroup2': self.create_random_name(prefix='app-group-nscli2', length=20),
            'appgroup3': self.create_random_name(prefix='app-group-nscli3', length=20),
            'appgroup4': self.create_random_name(prefix='app-group-nscli4', length=20),
            'identifier1': 'SASKeyName=' + self.create_random_name(prefix='saskey', length=24),
            'identifier2': 'SASKeyName=' + self.create_random_name(prefix='saskey', length=24),
            'identifier3': 'SASKeyName=' + self.create_random_name(prefix='saskey', length=24)
        })
        from azure.cli.core import CLIError

        self.cmd('eventhubs namespace create --resource-group {rg} --name {namespacename} --location {loc} --sku Premium')

        AppGroup = self.cmd('eventhubs namespace application-group create --resource-group {rg} --namespace-name {namespacename} '
                            '--name {appgroup1} --client-app-group-identifier {identifier1} --is-enabled true '
                            '--throttling-policy-config name=policy1 rate-limit-threshold=10000 metric-id=IncomingBytes '
                            '--throttling-policy-config name=policy2 rate-limit-threshold=15000 metric-id=outgoingMessages '
                            '--throttling-policy-config name=policy3 rate-limit-threshold=10000 metric-id=IncomingMessages').get_output_in_json()

        self.assertEqual(self.kwargs['appgroup1'], AppGroup['name'])
        self.assertEqual(self.kwargs['identifier1'], AppGroup['clientAppGroupIdentifier'])
        self.assertEqual(True, AppGroup['isEnabled'])
        n = [i for i in AppGroup['policies']]
        assert len(n) == 3
        self.assertEqual('policy1', AppGroup['policies'][0]['name'])
        self.assertEqual('IncomingBytes', AppGroup['policies'][0]['metricId'])
        self.assertEqual(10000, AppGroup['policies'][0]['rateLimitThreshold'])
        self.assertEqual('policy2', AppGroup['policies'][1]['name'])
        self.assertEqual('OutgoingMessages', AppGroup['policies'][1]['metricId'])
        self.assertEqual(15000, AppGroup['policies'][1]['rateLimitThreshold'])
        self.assertEqual('policy3', AppGroup['policies'][2]['name'])
        self.assertEqual('IncomingMessages', AppGroup['policies'][2]['metricId'])
        self.assertEqual(10000, AppGroup['policies'][2]['rateLimitThreshold'])

        AppGroup = self.cmd(
            'eventhubs namespace application-group policy add --resource-group {rg} --namespace-name {namespacename} '
            '--name {appgroup1} '
            '--throttling-policy-config name=policy4 rate-limit-threshold=19000 metric-id=outgoingbytes').get_output_in_json()

        self.assertEqual(self.kwargs['appgroup1'], AppGroup['name'])
        self.assertEqual(self.kwargs['identifier1'], AppGroup['clientAppGroupIdentifier'])
        self.assertEqual(True, AppGroup['isEnabled'])
        n = [i for i in AppGroup['policies']]
        assert len(n) == 4
        self.assertEqual('policy1', AppGroup['policies'][0]['name'])
        self.assertEqual('IncomingBytes', AppGroup['policies'][0]['metricId'])
        self.assertEqual(10000, AppGroup['policies'][0]['rateLimitThreshold'])
        self.assertEqual('policy2', AppGroup['policies'][1]['name'])
        self.assertEqual('OutgoingMessages', AppGroup['policies'][1]['metricId'])
        self.assertEqual(15000, AppGroup['policies'][1]['rateLimitThreshold'])
        self.assertEqual('policy3', AppGroup['policies'][2]['name'])
        self.assertEqual('IncomingMessages', AppGroup['policies'][2]['metricId'])
        self.assertEqual(10000, AppGroup['policies'][2]['rateLimitThreshold'])
        self.assertEqual('policy4', AppGroup['policies'][3]['name'])
        self.assertEqual('OutgoingBytes', AppGroup['policies'][3]['metricId'])
        self.assertEqual(19000, AppGroup['policies'][3]['rateLimitThreshold'])

        AppGroup = self.cmd(
            'eventhubs namespace application-group policy remove --resource-group {rg} --namespace-name {namespacename} '
            '--name {appgroup1} '
            '--throttling-policy-config name=policy4 rate-limit-threshold=19000 metric-id=OutgoingBytes').get_output_in_json()

        self.assertEqual(self.kwargs['appgroup1'], AppGroup['name'])
        self.assertEqual(self.kwargs['identifier1'], AppGroup['clientAppGroupIdentifier'])
        self.assertEqual(True, AppGroup['isEnabled'])
        n = [i for i in AppGroup['policies']]
        assert len(n) == 3
        self.assertEqual('policy1', AppGroup['policies'][0]['name'])
        self.assertEqual('IncomingBytes', AppGroup['policies'][0]['metricId'])
        self.assertEqual(10000, AppGroup['policies'][0]['rateLimitThreshold'])
        self.assertEqual('policy2', AppGroup['policies'][1]['name'])
        self.assertEqual('OutgoingMessages', AppGroup['policies'][1]['metricId'])
        self.assertEqual(15000, AppGroup['policies'][1]['rateLimitThreshold'])
        self.assertEqual('policy3', AppGroup['policies'][2]['name'])
        self.assertEqual('IncomingMessages', AppGroup['policies'][2]['metricId'])
        self.assertEqual(10000, AppGroup['policies'][2]['rateLimitThreshold'])

        AppGroup = self.cmd(
            'eventhubs namespace application-group policy remove --resource-group {rg} --namespace-name {namespacename} '
            '--name {appgroup1} '
            '--throttling-policy-config name=policy2 rate-limit-threshold=15000 metric-id=outgoingMessages '
            '--throttling-policy-config name=policy3 rate-limit-threshold=10000 metric-id=IncomingMessages').get_output_in_json()

        self.assertEqual(self.kwargs['appgroup1'], AppGroup['name'])
        self.assertEqual(self.kwargs['identifier1'], AppGroup['clientAppGroupIdentifier'])
        self.assertEqual(True, AppGroup['isEnabled'])
        n = [i for i in AppGroup['policies']]
        assert len(n) == 1
        self.assertEqual('policy1', AppGroup['policies'][0]['name'])
        self.assertEqual('IncomingBytes', AppGroup['policies'][0]['metricId'])
        self.assertEqual(10000, AppGroup['policies'][0]['rateLimitThreshold'])

        AppGroup = self.cmd(
            'eventhubs namespace application-group policy add --resource-group {rg} --namespace-name {namespacename} '
            '--name {appgroup1} '
            '--throttling-policy-config name=policy2 rate-limit-threshold=15000 metric-id=outgoingMessages '
            '--throttling-policy-config name=policy3 rate-limit-threshold=12000 metric-id=IncomingMessages').get_output_in_json()

        self.assertEqual(self.kwargs['appgroup1'], AppGroup['name'])
        self.assertEqual(self.kwargs['identifier1'], AppGroup['clientAppGroupIdentifier'])
        self.assertEqual(True, AppGroup['isEnabled'])
        n = [i for i in AppGroup['policies']]
        assert len(n) == 3
        self.assertEqual('policy1', AppGroup['policies'][0]['name'])
        self.assertEqual('IncomingBytes', AppGroup['policies'][0]['metricId'])
        self.assertEqual(10000, AppGroup['policies'][0]['rateLimitThreshold'])
        self.assertEqual('policy2', AppGroup['policies'][1]['name'])
        self.assertEqual('OutgoingMessages', AppGroup['policies'][1]['metricId'])
        self.assertEqual(15000, AppGroup['policies'][1]['rateLimitThreshold'])
        self.assertEqual('policy3', AppGroup['policies'][2]['name'])
        self.assertEqual('IncomingMessages', AppGroup['policies'][2]['metricId'])
        self.assertEqual(12000, AppGroup['policies'][2]['rateLimitThreshold'])

        AppGroup = self.cmd('eventhubs namespace application-group show --resource-group {rg} --namespace-name {namespacename} --name {appgroup1}').get_output_in_json()

        self.assertEqual(self.kwargs['appgroup1'], AppGroup['name'])
        self.assertEqual(self.kwargs['identifier1'], AppGroup['clientAppGroupIdentifier'])
        self.assertEqual(True, AppGroup['isEnabled'])
        n = [i for i in AppGroup['policies']]
        assert len(n) == 3
        self.assertEqual('policy1', AppGroup['policies'][0]['name'])
        self.assertEqual('IncomingBytes', AppGroup['policies'][0]['metricId'])
        self.assertEqual(10000, AppGroup['policies'][0]['rateLimitThreshold'])
        self.assertEqual('policy2', AppGroup['policies'][1]['name'])
        self.assertEqual('OutgoingMessages', AppGroup['policies'][1]['metricId'])
        self.assertEqual(15000, AppGroup['policies'][1]['rateLimitThreshold'])
        self.assertEqual('policy3', AppGroup['policies'][2]['name'])
        self.assertEqual('IncomingMessages', AppGroup['policies'][2]['metricId'])
        self.assertEqual(12000, AppGroup['policies'][2]['rateLimitThreshold'])

        AppGroup = self.cmd('eventhubs namespace application-group update --resource-group {rg} --namespace-name {namespacename} --name {appgroup1} '
                            '--is-enabled false').get_output_in_json()

        self.assertEqual(self.kwargs['appgroup1'], AppGroup['name'])
        self.assertEqual(self.kwargs['identifier1'], AppGroup['clientAppGroupIdentifier'])
        self.assertEqual(False, AppGroup['isEnabled'])
        n = [i for i in AppGroup['policies']]
        assert len(n) == 3
        self.assertEqual('policy1', AppGroup['policies'][0]['name'])
        self.assertEqual('IncomingBytes', AppGroup['policies'][0]['metricId'])
        self.assertEqual(10000, AppGroup['policies'][0]['rateLimitThreshold'])
        self.assertEqual('policy2', AppGroup['policies'][1]['name'])
        self.assertEqual('OutgoingMessages', AppGroup['policies'][1]['metricId'])
        self.assertEqual(15000, AppGroup['policies'][1]['rateLimitThreshold'])
        self.assertEqual('policy3', AppGroup['policies'][2]['name'])
        self.assertEqual('IncomingMessages', AppGroup['policies'][2]['metricId'])
        self.assertEqual(12000, AppGroup['policies'][2]['rateLimitThreshold'])

        AppGroup = self.cmd(
            'eventhubs namespace application-group update --resource-group {rg} --namespace-name {namespacename} --name {appgroup1} '
            '--is-enabled').get_output_in_json()

        self.assertEqual(self.kwargs['appgroup1'], AppGroup['name'])
        self.assertEqual(self.kwargs['identifier1'], AppGroup['clientAppGroupIdentifier'])
        self.assertEqual(True, AppGroup['isEnabled'])
        n = [i for i in AppGroup['policies']]
        assert len(n) == 3
        self.assertEqual('policy1', AppGroup['policies'][0]['name'])
        self.assertEqual('IncomingBytes', AppGroup['policies'][0]['metricId'])
        self.assertEqual(10000, AppGroup['policies'][0]['rateLimitThreshold'])
        self.assertEqual('policy2', AppGroup['policies'][1]['name'])
        self.assertEqual('OutgoingMessages', AppGroup['policies'][1]['metricId'])
        self.assertEqual(15000, AppGroup['policies'][1]['rateLimitThreshold'])
        self.assertEqual('policy3', AppGroup['policies'][2]['name'])
        self.assertEqual('IncomingMessages', AppGroup['policies'][2]['metricId'])
        self.assertEqual(12000, AppGroup['policies'][2]['rateLimitThreshold'])

        AppGroup = self.cmd(
            'eventhubs namespace application-group create --resource-group {rg} --namespace-name {namespacename} '
            '--name {appgroup2} --client-app-group-identifier {identifier2} '
            '--throttling-policy-config name=policy1 rate-limit-threshold=10000 metric-id=IncomingBytes '
            '--throttling-policy-config name=policy2 rate-limit-threshold=15000 metric-id=outgoingMessages '
            '--throttling-policy-config name=policy3 rate-limit-threshold=10000 metric-id=IncomingMessages '
            '--throttling-policy-config name=policy4 rate-limit-threshold=182000 metric-id=outgoingbytes').get_output_in_json()

        self.assertEqual(self.kwargs['appgroup2'], AppGroup['name'])
        self.assertEqual(self.kwargs['identifier2'], AppGroup['clientAppGroupIdentifier'])
        self.assertEqual(True, AppGroup['isEnabled'])
        n = [i for i in AppGroup['policies']]
        assert len(n) == 4
        self.assertEqual('policy1', AppGroup['policies'][0]['name'])
        self.assertEqual('IncomingBytes', AppGroup['policies'][0]['metricId'])
        self.assertEqual(10000, AppGroup['policies'][0]['rateLimitThreshold'])
        self.assertEqual('policy2', AppGroup['policies'][1]['name'])
        self.assertEqual('OutgoingMessages', AppGroup['policies'][1]['metricId'])
        self.assertEqual(15000, AppGroup['policies'][1]['rateLimitThreshold'])
        self.assertEqual('policy3', AppGroup['policies'][2]['name'])
        self.assertEqual('IncomingMessages', AppGroup['policies'][2]['metricId'])
        self.assertEqual(10000, AppGroup['policies'][2]['rateLimitThreshold'])
        self.assertEqual('policy4', AppGroup['policies'][3]['name'])
        self.assertEqual('OutgoingBytes', AppGroup['policies'][3]['metricId'])
        self.assertEqual(182000, AppGroup['policies'][3]['rateLimitThreshold'])

        with self.assertRaisesRegex(CLIError, 'The following policy was not found: Name: policy4, RateLimitThreshold: 10000, MetricId: OutgoingBytes'):
            self.cmd('eventhubs namespace application-group policy remove --resource-group {rg} --namespace-name {namespacename} --name {appgroup2} '
                     '--throttling-policy-config name=policy4 rate-limit-threshold=10000 metric-id=outgoingbytes')

        with self.assertRaisesRegex(CLIError, 'The following policy was not found: Name: policy4, RateLimitThreshold: 182000, MetricId: OutgoingMessages'):
            self.cmd('eventhubs namespace application-group policy remove --resource-group {rg} --namespace-name {namespacename} --name {appgroup2} '
                     '--throttling-policy-config name=policy4 rate-limit-threshold=182000 metric-id=outgoingmessages',
                     checks=[
                     ])

        AppGroup = self.cmd(
                'eventhubs namespace application-group show --resource-group {rg} --namespace-name {namespacename} --name {appgroup2}').get_output_in_json()

        self.assertEqual(self.kwargs['appgroup2'], AppGroup['name'])
        self.assertEqual(self.kwargs['identifier2'], AppGroup['clientAppGroupIdentifier'])
        self.assertEqual(True, AppGroup['isEnabled'])
        n = [i for i in AppGroup['policies']]
        assert len(n) == 4
        self.assertEqual('policy1', AppGroup['policies'][0]['name'])
        self.assertEqual('IncomingBytes', AppGroup['policies'][0]['metricId'])
        self.assertEqual(10000, AppGroup['policies'][0]['rateLimitThreshold'])
        self.assertEqual('policy2', AppGroup['policies'][1]['name'])
        self.assertEqual('OutgoingMessages', AppGroup['policies'][1]['metricId'])
        self.assertEqual(15000, AppGroup['policies'][1]['rateLimitThreshold'])
        self.assertEqual('policy3', AppGroup['policies'][2]['name'])
        self.assertEqual('IncomingMessages', AppGroup['policies'][2]['metricId'])
        self.assertEqual(10000, AppGroup['policies'][2]['rateLimitThreshold'])
        self.assertEqual('policy4', AppGroup['policies'][3]['name'])
        self.assertEqual('OutgoingBytes', AppGroup['policies'][3]['metricId'])
        self.assertEqual(182000, AppGroup['policies'][3]['rateLimitThreshold'])

        AppGroup = self.cmd(
            'eventhubs namespace application-group policy remove --resource-group {rg} --namespace-name {namespacename} '
            '--name {appgroup2} '
            '--throttling-policy-config name=policy4 rate-limit-threshold=182000 metric-id=OutgoingBytes').get_output_in_json()

        self.assertEqual(self.kwargs['appgroup2'], AppGroup['name'])
        self.assertEqual(self.kwargs['identifier2'], AppGroup['clientAppGroupIdentifier'])
        self.assertEqual(True, AppGroup['isEnabled'])
        n = [i for i in AppGroup['policies']]
        assert len(n) == 3
        self.assertEqual('policy1', AppGroup['policies'][0]['name'])
        self.assertEqual('IncomingBytes', AppGroup['policies'][0]['metricId'])
        self.assertEqual(10000, AppGroup['policies'][0]['rateLimitThreshold'])
        self.assertEqual('policy2', AppGroup['policies'][1]['name'])
        self.assertEqual('OutgoingMessages', AppGroup['policies'][1]['metricId'])
        self.assertEqual(15000, AppGroup['policies'][1]['rateLimitThreshold'])
        self.assertEqual('policy3', AppGroup['policies'][2]['name'])
        self.assertEqual('IncomingMessages', AppGroup['policies'][2]['metricId'])
        self.assertEqual(10000, AppGroup['policies'][2]['rateLimitThreshold'])

        AppGroup = self.cmd(
            'eventhubs namespace application-group create --resource-group {rg} --namespace-name {namespacename} '
            '--name {appgroup3} --client-app-group-identifier {identifier3} '
            '--throttling-policy-config name=policy1 rate-limit-threshold=10000 metric-id=IncomingBytes').get_output_in_json()

        self.assertEqual(self.kwargs['appgroup3'], AppGroup['name'])
        self.assertEqual(self.kwargs['identifier3'], AppGroup['clientAppGroupIdentifier'])
        self.assertEqual(True, AppGroup['isEnabled'])
        n = [i for i in AppGroup['policies']]
        assert len(n) == 1
        self.assertEqual('policy1', AppGroup['policies'][0]['name'])
        self.assertEqual('IncomingBytes', AppGroup['policies'][0]['metricId'])
        self.assertEqual(10000, AppGroup['policies'][0]['rateLimitThreshold'])

        self.cmd('eventhubs namespace application-group delete --resource-group {rg} --namespace-name {namespacename} '
                 '--name {appgroup1}')

        time.sleep(20)

        list_of_app_groups = self.cmd('eventhubs namespace application-group list --resource-group {rg} --namespace-name {namespacename}').get_output_in_json()

        self.assertEqual(len(list_of_app_groups), 2)
