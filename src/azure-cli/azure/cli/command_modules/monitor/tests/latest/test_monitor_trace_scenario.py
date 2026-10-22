# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.azclierror import InvalidArgumentValueError
from azure.cli.testsdk import ResourceGroupPreparer, ScenarioTest

# Trace containers and Application Insights trace associations can only be created in regions with traces enabled.
# Canary regions get them first.
TRACE_LOCATION = 'eastus2euap'


def _scopes(associations):
    return [a['id'].lower().rsplit('/providers/microsoft.monitor/traceassociations/', 1)[0] for a in associations]


class TestMonitorTraceScenarios(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_monitor_trace_container', location=TRACE_LOCATION)
    def test_monitor_trace_container(self, resource_group):
        self.kwargs.update({'amw': self.create_random_name('amw', 12)})
        self.cmd('monitor account create -n {amw} -g {rg}')

        self.cmd('monitor account trace-container create -g {rg} -w {amw}', checks=[
            self.check_pattern('id', '(?i).*/traceContainers/default$'),
            self.check('properties.traceRetentionInDays', 30),
            self.check('properties.traceDurationWindowInSeconds', 600),
            self.check('properties.traceMetricsState', 'Enabled'),
        ])
        self.cmd('monitor account trace-container update -g {rg} -w {amw} --retention-days 60 --no-wait')
        self.cmd('monitor account trace-container wait -g {rg} -w {amw} --updated')
        # create keeps the current value of every setting it is not given
        self.cmd('monitor account trace-container create -g {rg} -w {amw} --trace-duration-window 300 '
                 '--trace-metrics Disabled', checks=[
                     self.check('properties.traceRetentionInDays', 60),
                     self.check('properties.traceDurationWindowInSeconds', 300),
                     self.check('properties.traceMetricsState', 'Disabled'),
                 ])
        self.cmd('monitor account trace-container show -g {rg} -w {amw}', checks=[
            self.check('properties.traceRetentionInDays', 60),
            self.check('properties.traceDurationWindowInSeconds', 300),
            self.check('properties.traceMetricsState', 'Disabled'),
        ])

    @ResourceGroupPreparer(name_prefix='cli_test_monitor_trace_association', location=TRACE_LOCATION)
    def test_monitor_trace_association(self, resource_group):
        subscription = self.get_subscription_id()
        self.kwargs.update({
            'amw': self.create_random_name('amw', 12),
            'amw2': self.create_random_name('amw', 12),
            'law': self.create_random_name('law', 12),
            'ai': self.create_random_name('ai', 12),
            'sub_id': '/subscriptions/' + subscription,
            'rg_id': '/subscriptions/{}/resourceGroups/{}'.format(subscription, resource_group),
        })
        self.kwargs['amw_id'] = self.cmd('monitor account create -n {amw} -g {rg}').get_output_in_json()['id']
        self.kwargs['law_id'] = self.cmd(
            'monitor log-analytics workspace create -g {rg} -n {law}').get_output_in_json()['id']
        # Application Insights is not offered in canary regions. Trace association creation is gated on the region of
        # the component's Log Analytics workspace, so the component uses the canary workspace from another region.
        self.kwargs['ai_id'] = self.cmd(
            'resource create -g {rg} -n {ai} --resource-type microsoft.insights/components --is-full-object '
            '--properties \'{{"kind": "web", "location": "eastus2", '
            '"properties": {{"Application_Type": "web", "WorkspaceResourceId": "{law_id}"}}}}\''
        ).get_output_in_json()['id']

        with self.assertRaisesRegex(InvalidArgumentValueError, '--resource-uri must be'):
            self.cmd('monitor trace-association show --resource-uri {amw_id}')

        # A resource group association creates the trace container of the workspace with the given settings.
        result = self.cmd('monitor trace-association create --resource-uri {rg_id} --azure-monitor-workspace {amw_id} '
                          '--trace-retention-days 60 --trace-metrics Disabled').get_output_in_json()
        self.assertEqual(result['properties']['azureMonitorWorkspaceResourceId'].lower(), self.kwargs['amw_id'].lower())
        self.cmd('monitor account trace-container show -g {rg} -w {amw}', checks=[
            self.check('properties.traceRetentionInDays', 60),
            self.check('properties.traceMetricsState', 'Disabled'),
        ])
        with self.assertRaisesRegex(InvalidArgumentValueError, 'already exists'):
            self.cmd('monitor trace-association create --resource-uri {rg_id} -w {amw_id} --trace-retention-days 90')
        self.cmd('monitor trace-association show --resource-uri {rg_id}', checks=[
            self.check_pattern('id', '(?i).*/traceAssociations/default$'),
        ])

        # An Application Insights component adds its own association to the one it inherits.
        self.cmd('monitor trace-association create --resource-uri {ai_id} -w {amw_id}')
        associations = self.cmd('monitor trace-association list --resource-uri {ai_id}').get_output_in_json()
        self.assertEqual(_scopes(associations)[:2], [self.kwargs['ai_id'].lower(), self.kwargs['rg_id'].lower()])

        # Replacing the workspace of a resource group creates the trace container of the new workspace.
        self.kwargs['amw2_id'] = self.cmd('monitor account create -n {amw2} -g {rg}').get_output_in_json()['id']
        self.cmd('monitor trace-association create --resource-uri {rg_id} -w {amw2_id} --yes')
        self.cmd('monitor account trace-container show -g {rg} -w {amw2}', checks=[
            self.check('properties.traceRetentionInDays', 30),
            self.check('properties.traceMetricsState', 'Enabled'),
        ])
        associations = self.cmd('monitor trace-association list --resource-uri {ai_id}').get_output_in_json()
        self.assertEqual(associations[1]['properties']['azureMonitorWorkspaceResourceId'].lower(),
                         self.kwargs['amw2_id'].lower())

        self.cmd('monitor trace-association delete --resource-uri {ai_id}')
        self.cmd('monitor trace-association delete --resource-uri {rg_id} --yes')
        # Deleting again is a no-op that does not ask for confirmation.
        self.cmd('monitor trace-association delete --resource-uri {rg_id}')
        self.cmd('monitor trace-association show --resource-uri {rg_id}', expect_failure=True)
        associations = self.cmd('monitor trace-association list --resource-uri {ai_id}').get_output_in_json()
        self.assertNotIn(self.kwargs['rg_id'].lower(), _scopes(associations))
        self.cmd('monitor trace-association list --resource-uri {sub_id}')
