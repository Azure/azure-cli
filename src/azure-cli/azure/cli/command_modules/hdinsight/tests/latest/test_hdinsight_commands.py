# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


import os

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer
from azure.cli.testsdk.scenario_tests import record_only

TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))


class HDInsightClusterTests(ScenarioTest):
    location = 'southcentralus'

    # Uses 'rg' kwarg
    @ResourceGroupPreparer(name_prefix='hdicli-', location=location, random_name_length=12)
    @StorageAccountPreparer(name_prefix='hdicli', location=location, parameter_name='storage_account')
    def test_hdinsight_cluster_min_args(self, storage_account_info):
        self._create_hdinsight_cluster(self._wasb_arguments(storage_account_info,
                                                            specify_key=False, specify_container=False))

    # Uses 'rg' kwarg
    @ResourceGroupPreparer(name_prefix='hdicli-', location=location, random_name_length=12)
    @StorageAccountPreparer(name_prefix='hdicli', location=location, parameter_name='storage_account')
    def test_hdinsight_cluster_resize(self, storage_account_info):
        self._create_hdinsight_cluster(
            self._wasb_arguments(storage_account_info))

        resize_cluster_format = 'az hdinsight resize -n {cluster} -g {rg} --workernode-count 2'
        self.cmd(resize_cluster_format)

        self.cmd('az hdinsight show -n {cluster} -g {rg}', checks=[
            self.check('properties.provisioningState', 'Succeeded'),
            self.check('properties.clusterState', 'Running'),
            self.check(
                "properties.computeProfile.roles[?name=='workernode'].targetInstanceCount", [2])
        ])

    # Uses 'rg' kwarg
    @ResourceGroupPreparer(name_prefix='hdicli-', location=location, random_name_length=12)
    @StorageAccountPreparer(name_prefix='hdicli', location=location, parameter_name='storage_account')
    def test_hdinsight_cluster_kafka(self, storage_account_info):
        self._create_hdinsight_cluster(
            HDInsightClusterTests._wasb_arguments(storage_account_info),
            HDInsightClusterTests._kafka_arguments()
        )

    # Uses 'rg' kwarg
    # _rest_proxy_arguments() will override location to southcentralus, so use this location for rg and sa
    @ResourceGroupPreparer(name_prefix='hdicli-', location='southcentralus', random_name_length=12)
    @StorageAccountPreparer(name_prefix='hdicli', location='southcentralus', parameter_name='storage_account')
    def test_hdinsight_cluster_kafka_with_rest_proxy(self, storage_account_info):
        self._create_hdinsight_cluster(
            HDInsightClusterTests._wasb_arguments(storage_account_info),
            HDInsightClusterTests._kafka_arguments(),
            HDInsightClusterTests._rest_proxy_arguments()
        )

    # Uses 'rg' kwarg
    @ResourceGroupPreparer(name_prefix='hdicli-', location=location, random_name_length=12)
    @StorageAccountPreparer(name_prefix='hdicli', location=location, parameter_name='storage_account')
    def test_hdinsight_cluster_kafka_with_optional_disk_args(self, storage_account_info):
        self._create_hdinsight_cluster(
            HDInsightClusterTests._wasb_arguments(storage_account_info),
            HDInsightClusterTests._kafka_arguments(),
            HDInsightClusterTests._optional_data_disk_arguments()
        )

    # Uses 'rg' kwarg
    @ResourceGroupPreparer(name_prefix='hdicli-', location=location, random_name_length=12)
    @StorageAccountPreparer(name_prefix='hdicli', location=location, parameter_name='storage_account')
    def test_hdinsight_cluster_with_component_version(self, storage_account_info):
        self._create_hdinsight_cluster(
            HDInsightClusterTests._wasb_arguments(storage_account_info),
            HDInsightClusterTests._component_version_arguments()
        )

    # Uses 'rg' kwarg
    @ResourceGroupPreparer(name_prefix='hdicli-', location=location, random_name_length=12)
    @StorageAccountPreparer(name_prefix='hdicli', location=location, parameter_name='storage_account')
    def test_hdinsight_cluster_with_cluster_config(self, storage_account_info):
        self._create_hdinsight_cluster(
            HDInsightClusterTests._wasb_arguments(storage_account_info),
            HDInsightClusterTests._with_cluster_config()
        )

    # Uses 'rg' kwarg
    @ResourceGroupPreparer(name_prefix='hdicli-', location=location, random_name_length=12)
    @StorageAccountPreparer(name_prefix='hdicli', location=location, parameter_name='storage_account')
    def test_hdinsight_cluster_with_ssh_creds(self, storage_account_info):
        self._create_hdinsight_cluster(
            HDInsightClusterTests._wasb_arguments(storage_account_info),
            HDInsightClusterTests._with_explicit_ssh_creds()
        )

    @ResourceGroupPreparer(name_prefix='hdicli-', location=location, random_name_length=12)
    @StorageAccountPreparer(name_prefix='hdicli', location=location, parameter_name='storage_account')
    def test_hdinsight_cluster_with_minimal_tls_version(self, storage_account_info):
        self._create_hdinsight_cluster(
            HDInsightClusterTests._wasb_arguments(storage_account_info),
            HDInsightClusterTests._with_minimal_tls_version('1.2')
        )

        self.cmd('az hdinsight show -n {cluster} -g {rg}', checks=[
            self.check('properties.minSupportedTlsVersion', '1.2'),
            self.check('properties.clusterState', 'Running')
        ])

    @ResourceGroupPreparer(name_prefix='hdicli-', location=location, random_name_length=12)
    @StorageAccountPreparer(name_prefix='hdicli', location=location, parameter_name='storage_account')
    def test_hdinsight_cluster_with_encryption_in_transit(self, storage_account_info):
        self._create_hdinsight_cluster(
            HDInsightClusterTests._wasb_arguments(storage_account_info),
            HDInsightClusterTests._with_encryption_in_transit()
        )

        self.cmd('az hdinsight show -n {cluster} -g {rg}', checks=[
            self.check('properties.encryptionInTransitProperties.isEncryptionInTransitEnabled', True),
            self.check('properties.clusterState', 'Running')
        ])

    @ResourceGroupPreparer(name_prefix='hdicli-', location=location, random_name_length=12)
    @StorageAccountPreparer(name_prefix='hdicli', location=location, parameter_name='storage_account')
    def test_hdinsight_cluster_with_loadbased_autoscale(self, storage_account_info):
        self._create_hdinsight_cluster(
            HDInsightClusterTests._wasb_arguments(storage_account_info),
            HDInsightClusterTests._with_load_based_autoscale()
        )
        self.cmd('az hdinsight show -n {cluster} -g {rg}', checks=[
            self.check('properties.clusterState', 'Running'),
            self.check(
                "properties.computeProfile.roles[?name=='workernode'].autoscaleConfiguration.capacity.minInstanceCount",
                [4])
        ])

    @ResourceGroupPreparer(name_prefix='hdicli-', location=location, random_name_length=12)
    @StorageAccountPreparer(name_prefix='hdicli', location=location, parameter_name='storage_account')
    def test_hdinsight_cluster_with_schedulebased_autoscale(self, storage_account_info):
        self._create_hdinsight_cluster(
            HDInsightClusterTests._wasb_arguments(storage_account_info),
            HDInsightClusterTests._with_schedule_based_autoscale()
        )
        self.cmd('az hdinsight show -n {cluster} -g {rg}', checks=[
            self.check('properties.clusterState', 'Running'),
            self.check(
                "properties.computeProfile.roles[?name=='workernode'].autoscaleConfiguration.recurrence."
                "schedule[0].timeAndCapacity.minInstanceCount",
                [5])
        ])

    @ResourceGroupPreparer(name_prefix='hdicli-', location=location, random_name_length=12)
    @StorageAccountPreparer(name_prefix='hdicli', location=location, parameter_name='storage_account')
    def test_hdinsight_cluster_with_encryption_at_host(self, storage_account_info):
        self._create_hdinsight_cluster(
            HDInsightClusterTests._wasb_arguments(storage_account_info),
            HDInsightClusterTests._with_encryption_at_host()
        )

        self.cmd('az hdinsight show -n {cluster} -g {rg}', checks=[
            self.check('properties.diskEncryptionProperties.encryptionAtHost', True),
            self.check('properties.clusterState', 'Running')
        ])

    @ResourceGroupPreparer(name_prefix='hdicli-', location=location, random_name_length=12)
    @StorageAccountPreparer(name_prefix='hdicli', location=location, parameter_name='storage_account')
    def test_hdinsight_cluster_with_private_link_configurations(self, storage_account_info):
        self.kwargs.update(
            {
                'private_link_config_file_path': os.path.join(TEST_DIR, 'privatelinkconfigurations.json')
            }
        )
        self._create_hdinsight_cluster(
            HDInsightClusterTests._wasb_arguments(storage_account_info),
            HDInsightClusterTests._with_private_link_configurations(self.kwargs['private_link_config_file_path'])
        )

        self.cmd('az hdinsight show -n {cluster} -g {rg}', checks=[
            self.check('properties.networkProperties.privateLink', "Enabled"),
            self.check('properties.networkProperties.resourceProviderConnection', 'Outbound'),
            self.check('type(properties.privateLinkConfigurations)', 'array'),
            self.check('length(properties.privateLinkConfigurations)', 1),
        ])

    @ResourceGroupPreparer(name_prefix='hdicli-', location=location, random_name_length=12)
    @StorageAccountPreparer(name_prefix='hdicli', location=location, parameter_name='storage_account')
    def test_hdinsight_cluster_with_compute_isolation(self, storage_account_info):
        self._create_hdinsight_cluster(
            HDInsightClusterTests._wasb_arguments(storage_account_info),
            HDInsightClusterTests._with_compute_isolation()
        )
        self.cmd('az hdinsight show -n {cluster} -g {rg}', checks=[
            self.check('properties.computeIsolationProperties.enableComputeIsolation', True)
        ])


    @ResourceGroupPreparer(name_prefix='hdicli-', location=location, random_name_length=12)
    @StorageAccountPreparer(name_prefix='hdicli', location=location, parameter_name='storage_account')
    def test_hdinsight_cluster_with_availability_zones(self, storage_account_info):
        self.kwargs.update(
            {
                'custom_all_meta_stores_file_path': os.path.join(TEST_DIR, 'customallmetastores.json')
            }
        )
        self._create_hdinsight_cluster(
            HDInsightClusterTests._wasb_arguments(storage_account_info),
            HDInsightClusterTests._with_availability_zones(self.kwargs['custom_all_meta_stores_file_path'])
        )

        self.cmd('az hdinsight show -n {cluster} -g {rg}', checks=[
            self.check('type(zones)', 'array'),
            self.check('length(zones)', 1),
        ])


    # Uses 'rg' kwarg
    @ResourceGroupPreparer(name_prefix='hdicli-', location=location, random_name_length=12)
    @StorageAccountPreparer(name_prefix='hdicli', location=location, parameter_name='storage_account')
    def test_hdinsight_application(self, storage_account_info):
        self._create_hdinsight_cluster(
            HDInsightClusterTests._wasb_arguments(storage_account_info),
            HDInsightClusterTests._with_explicit_ssh_creds()
        )

        # define application item names
        self.kwargs.update({
            'app': self.create_random_name(prefix='hdicliapp-', length=16),
            'script_uri': 'https://hdiconfigactions.blob.core.windows.net/linuxhueconfigactionv02/install-hue-uber-v02.sh',
            'script_action': 'InstallHue',
            'script_params': '"-version latest -port 20000"'
        })

        # create an application and wait for completion
        self.cmd('az hdinsight application create -g {rg} -n {app} --cluster-name {cluster} '
                 '--script-uri {script_uri} --script-action-name {script_action} --script-parameters {script_params}')
        self.cmd('az hdinsight application wait --created -n {app} -g {rg} --cluster-name {cluster}')

        # list all applications
        self.cmd('az hdinsight application list -g {rg} --cluster-name {cluster}', checks=[
            self.check('type(@)', 'array'),
            self.check('length(@)', 1)
        ])

        # get the specific application
        self.cmd('az hdinsight application show -g {rg} -n {app} --cluster-name {cluster}', checks=[
            self.check('name', '{app}'),
            self.check('properties.provisioningState', 'Succeeded'),
            self.check('properties.applicationState', 'Running')
        ])

    # Uses 'rg' kwarg
    @ResourceGroupPreparer(name_prefix='hdicli-', location=location, random_name_length=12)
    @StorageAccountPreparer(name_prefix='hdicli', location=location, parameter_name='storage_account')
    def test_hdinsight_usage(self, storage_account_info):
        self.kwargs.update({
            'loc': self.location
        })

        self.cmd('az hdinsight list-usage -l {loc}', checks=[
            self.check('type(value)', 'array'),
            self.check('length(value)', 1)
        ])

    # Uses 'rg' kwarg
    @ResourceGroupPreparer(name_prefix='hdicli-', location=location, random_name_length=12)
    @StorageAccountPreparer(name_prefix='hdicli', location=location, parameter_name='storage_account')
    def test_hdinsight_monitor(self, storage_account_info):
        self.kwargs.update({
            'ws': self.create_random_name('testws', 20),
            'la_prop_path': os.path.join(TEST_DIR, 'loganalytics.json')
        })

        ws_response = self.cmd('resource create -g {rg} -n {ws} '
                               '--resource-type Microsoft.OperationalInsights/workspaces -p @"{la_prop_path}"') \
            .get_output_in_json()
        ws_customer_id = ws_response['properties']['customerId']

        self._create_hdinsight_cluster(
            HDInsightClusterTests._wasb_arguments(storage_account_info),
            HDInsightClusterTests._with_explicit_ssh_creds()
        )

        # get monitor status
        self.cmd('az hdinsight monitor show -g {rg} -n {cluster}', checks=[
            self.check('clusterMonitoringEnabled', False),
            self.check('workspaceId', None)
        ])

        # enable monitoring
        self.cmd('az hdinsight monitor enable -g {rg} -n {cluster} --workspace {ws} --no-validation-timeout')

        # get monitor status
        self.cmd('az hdinsight monitor show -g {rg} -n {cluster}', checks=[
            self.check('clusterMonitoringEnabled', True),
            self.check('workspaceId', ws_customer_id)
        ])

        # disable monitor
        self.cmd('az hdinsight monitor disable -g {rg} -n {cluster}')

        # get monitor status
        self.cmd('az hdinsight monitor show -g {rg} -n {cluster}', checks=[
            self.check('clusterMonitoringEnabled', False),
            self.check('workspaceId', None)
        ])

    # Uses 'rg' kwarg
    @ResourceGroupPreparer(name_prefix='hdicli-', location=location, random_name_length=12)
    @StorageAccountPreparer(name_prefix='hdicli', location=location, parameter_name='storage_account')
    def test_hdinsight_azure_monitor(self, storage_account_info):
        self.kwargs.update({
            'ws': self.create_random_name('testws', 20),
            'la_prop_path': os.path.join(TEST_DIR, 'loganalytics.json')
        })

        ws_response = self.cmd('resource create -g {rg} -n {ws} '
                               '--resource-type Microsoft.OperationalInsights/workspaces -p @"{la_prop_path}"') \
            .get_output_in_json()
        ws_customer_id = ws_response['properties']['customerId']

        self._create_hdinsight_cluster(
            HDInsightClusterTests._wasb_arguments(storage_account_info),
            HDInsightClusterTests._with_explicit_ssh_creds()
        )

        # get monitor status
        self.cmd('az hdinsight azure-monitor show -g {rg} -n {cluster}', checks=[
            self.check('clusterMonitoringEnabled', False),
            self.check('workspaceId', None)
        ])

        # enable monitoring
        self.cmd('az hdinsight azure-monitor enable -g {rg} -n {cluster} --workspace {ws} --no-validation-timeout')

        # get monitor status
        self.cmd('az hdinsight azure-monitor show -g {rg} -n {cluster}', checks=[
            self.check('clusterMonitoringEnabled', True),
            self.check('workspaceId', ws_customer_id)
        ])

        # disable monitor
        self.cmd('az hdinsight azure-monitor disable -g {rg} -n {cluster}')

        # get monitor status
        self.cmd('az hdinsight azure-monitor show -g {rg} -n {cluster}', checks=[
            self.check('clusterMonitoringEnabled', False),
            self.check('workspaceId', None)
        ])

    # Uses 'rg' kwarg
    @ResourceGroupPreparer(name_prefix='hdicli-', location=location, random_name_length=12)
    @StorageAccountPreparer(name_prefix='hdicli', location=location, parameter_name='storage_account')
    def test_hdinsight_script_action(self, storage_account_info):
        self.kwargs.update({
            'script_uri': 'https://hdiconfigactions.blob.core.windows.net/linuxgiraphconfigactionv01/giraph-installer-v01.sh',
            'script_action': 'InstallGiraph',
            'script_action_1': 'InstallGiraph1',
            'head_node': 'headnode',
            'worker_node': 'workernode'
        })

        self._create_hdinsight_cluster(
            HDInsightClusterTests._wasb_arguments(storage_account_info),
            HDInsightClusterTests._with_explicit_ssh_creds()
        )

        # execute script actions, and persist on success.
        self.cmd('az hdinsight script-action execute -g {rg} -n {script_action} '
                 '--cluster-name {cluster} --script-uri {script_uri} --roles {head_node} {worker_node} --persist-on-success')

        # list script actions and validate script is persisted.
        roles = [self.kwargs['head_node'], self.kwargs['worker_node']]
        self.cmd('az hdinsight script-action list -g {rg} --cluster-name {cluster}', checks=[
            self.check('type(@)', 'array'),
            self.check('length(@)', 1),
            self.check('[0].name', '{script_action}'),
            self.check('[0].uri', '{script_uri}'),
            self.check('[0].roles', roles)
        ])

        # delete script action.
        self.cmd('az hdinsight script-action delete -g {rg} -n {script_action} --cluster-name {cluster}')

        # list script actions and validate script is deleted.
        self.cmd('az hdinsight script-action list -g {rg} --cluster-name {cluster}', checks=[
            self.check('type(@)', 'array'),
            self.check('length(@)', 0)
        ])

        # list script action history and validate script appears there.
        script_actions = self.cmd('az hdinsight script-action list-execution-history -g {rg} --cluster-name {cluster}',
                                  checks=[
                                      self.check('type(@)', 'array'),
                                      self.check('length(@)', 1),
                                      self.check('[0].name', '{script_action}'),
                                      self.check('[0].uri', '{script_uri}'),
                                      self.check('[0].roles', roles),
                                      self.check('[0].status', 'Succeeded')
                                  ]).get_output_in_json()

        # get the script action by ID and validate it's the same action.
        self.kwargs['script_execution_id'] = str(script_actions[0]['scriptExecutionId'])
        script_actions = self.cmd('az hdinsight script-action show-execution-details -g {rg} --cluster-name {cluster} '
                                  '--execution-id {script_execution_id}',
                                  checks=[
                                      self.check('name', '{script_action}')
                                  ])

        # execute script actions, but don't persist on success.
        self.cmd('az hdinsight script-action execute -g {rg} --cluster-name {cluster} '
                 '--name {script_action_1} --script-uri {script_uri} --roles {head_node} {worker_node}')

        # list script action history and validate the new script also appears.
        script_actions = self.cmd('az hdinsight script-action list-execution-history -g {rg} --cluster-name {cluster}',
                                  checks=[
                                      self.check('type(@)', 'array'),
                                      self.check('length(@)', 2),
                                      self.check('[0].name', '{script_action_1}'),
                                      self.check("[0].uri", '{script_uri}'),
                                      self.check("[0].status", 'Succeeded')
                                  ]).get_output_in_json()

        # promote non-persisted script.
        self.kwargs['script_execution_id'] = str(script_actions[0]['scriptExecutionId'])
        script_actions = self.cmd('az hdinsight script-action promote -g {rg} --cluster-name {cluster} '
                                  '--execution-id {script_execution_id}')

        # list script action list and validate the promoted script is the only one there.
        self.cmd('az hdinsight script-action list -g {rg} --cluster-name {cluster}', checks=[
            self.check('type(@)', 'array'),
            self.check('length(@)', 1),
            self.check('[0].name', '{script_action_1}'),
            self.check('[0].uri', '{script_uri}'),
            self.check('[0].roles', roles),
            self.check('[0].status', None)
        ])

        # list script action history and validate both scripts are there.
        script_actions = self.cmd('az hdinsight script-action list-execution-history -g {rg} --cluster-name {cluster}',
                                  checks=[
                                      self.check('type(@)', 'array'),
                                      self.check('length(@)', 2),
                                      self.check('[0].name', '{script_action_1}'),
                                      self.check("[0].uri", '{script_uri}'),
                                      self.check("[0].roles", roles),
                                      self.check("[0].status", 'Succeeded'),
                                      self.check('[1].name', '{script_action}'),
                                      self.check("[1].uri", '{script_uri}'),
                                      self.check("[1].roles", roles),
                                      self.check("[1].status", 'Succeeded')
                                  ])

    # @record_only()
    # @ResourceGroupPreparer(name_prefix='hdicli-', location=location, random_name_length=12)
    # @StorageAccountPreparer(name_prefix='hdicli', location=location, parameter_name='storage_account')
    # def test_hdinsight_virtual_machine(self, storage_account_info):
    #     self._create_hdinsight_cluster(
    #         HDInsightClusterTests._wasb_arguments(storage_account_info)
    #     )
    #
    #     # list hosts of the cluster
    #     host_list = self.cmd('az hdinsight host list --resource-group {rg} --cluster-name {cluster}', checks=[
    #         self.check('type(@)', 'array'),
    #         self.exists('[0].name')
    #     ]).get_output_in_json()
    #
    #     target_host = host_list[0]['name']
    #     for host in host_list:
    #         if host['name'].startswith('wn'):
    #             target_host = host['name']
    #             break
    #     self.kwargs['target_host'] = target_host
    #     # restart host of the cluster
    #     self.cmd(
    #         'az hdinsight host restart --resource-group {rg} --cluster-name {cluster} --host-names {target_host} --yes')

    @ResourceGroupPreparer(name_prefix='hdicli-', location=location, random_name_length=12)
    @StorageAccountPreparer(name_prefix='hdicli', location=location, parameter_name='storage_account')
    def test_hdinsight_autoscale_operation(self, storage_account_info):
        self._create_hdinsight_cluster(
            HDInsightClusterTests._wasb_arguments(storage_account_info)
        )

        # enable load-based autoscale
        self.cmd(
            'az hdinsight autoscale create --cluster-name {cluster} --resource-group {rg} --type Load '
            '--min-workernode-count 4 --max-workernode-count 5 --yes')
        self.cmd('az hdinsight show --name {cluster} --resource-group {rg}', checks=[
            self.exists("properties.computeProfile.roles[?name=='workernode'].autoscaleConfiguration"),
            self.check(
                "properties.computeProfile.roles[?name=='workernode'].autoscaleConfiguration.capacity.minInstanceCount",
                [4])
        ])

        # to get robust
        import time
        time.sleep(150)
        # update load-based autoscale
        self.cmd(
            'az hdinsight autoscale update --cluster-name {cluster} --resource-group {rg} --min-workernode-count 3')
        self.cmd('az hdinsight show --name {cluster} --resource-group {rg}', checks=[
            self.exists("properties.computeProfile.roles[?name=='workernode'].autoscaleConfiguration"),
            self.check(
                "properties.computeProfile.roles[?name=='workernode'].autoscaleConfiguration.capacity.minInstanceCount",
                [3])
        ])

        # show autoscale configuration
        self.cmd('az hdinsight autoscale show --cluster-name {cluster} --resource-group {rg}', checks=[
            self.check("capacity.minInstanceCount", 3)
        ])

        # disable autoscale
        self.cmd('az hdinsight autoscale delete --cluster-name {cluster} --resource-group {rg} --yes')
        self.cmd('az hdinsight show --name {cluster} --resource-group {rg}')

        # to get robust
        time.sleep(150)
        # enable schedule-based autoscale
        self.cmd(
            'az hdinsight autoscale create --cluster-name {cluster} --resource-group {rg} --type Schedule --timezone '
            '"China Standard Time" --days Monday --time 09:00 --workernode-count 4 --yes')
        self.cmd('az hdinsight autoscale show --cluster-name {cluster} --resource-group {rg}', checks=[
            self.check("recurrence.schedule[0].days", ["Monday"])
        ])

        time.sleep(120)
        # add a new schedule condition
        self.cmd(
            'az hdinsight autoscale condition create --cluster-name {cluster} --resource-group {rg} --days Tuesday '
            '--time 08:00 --workernode-count 5')
        self.cmd('az hdinsight autoscale show --cluster-name {cluster} --resource-group {rg}', checks=[
            self.check("recurrence.schedule[1].days", ["Tuesday"])
        ])

        time.sleep(120)
        # update schedule condition
        self.cmd(
            'az hdinsight autoscale condition update --cluster-name {cluster} --resource-group {rg} '
            '--index 1 --workernode-count 4')
        self.cmd('az hdinsight autoscale show --cluster-name {cluster} --resource-group {rg}', checks=[
            self.check("recurrence.schedule[1].timeAndCapacity.minInstanceCount", 4)
        ])

        # list schedule conditions
        self.cmd('az hdinsight autoscale condition list --cluster-name {cluster} --resource-group {rg}', checks=[
            self.check('length(@)', 2)
        ])

        time.sleep(120)
        # delete schedule condition
        self.cmd(
            'az hdinsight autoscale condition delete --cluster-name {cluster} --resource-group {rg} --index 1 --yes')
        self.cmd('az hdinsight autoscale condition list --cluster-name {cluster} --resource-group {rg}', checks=[
            self.check('length(@)', 1)
        ])

    def _create_hdinsight_cluster(self, *additional_create_arguments):
        self.kwargs.update({
            'loc': self.location,
            'cluster': self.create_random_name(prefix='hdicli-', length=16),
            'http_password': 'Password1!',
            'cluster_type': 'spark'
        })

        create_cluster_format = 'az hdinsight create -n {cluster} -g {rg} -l {loc} -p {http_password} -t {cluster_type} ' \
                                + '--no-validation-timeout ' \
                                + ' '.join(additional_create_arguments)

        # Wait some time to improve robustness
        if self.is_live or self.in_recording:
            import time
            time.sleep(60)

        self.cmd(create_cluster_format, checks=[
            self.check('properties.provisioningState', 'Succeeded'),
            self.check('properties.clusterState', 'Running'),
            self.check("properties.computeProfile.roles[?name=='headnode']"
                       ".osProfile.linuxOperatingSystemProfile.username", ['sshuser'])
        ])

        self.cmd('az hdinsight show -n {cluster} -g {rg}', checks=[
            self.check('properties.provisioningState', 'Succeeded'),
            self.check('properties.clusterState', 'Running')
        ])

    @staticmethod
    def _wasb_arguments(storage_account_info, specify_key=False, specify_container=True):
        storage_account_name, storage_account_key = storage_account_info
        storage_account_key = storage_account_key.strip()

        key_args = ' --storage-account-key "{}"'.format(storage_account_key) if specify_key else ""
        container_args = ' --storage-container {}'.format('default') if specify_container else ""

        return '--storage-account {}{}{}' \
            .format(storage_account_name, key_args, container_args)

    @staticmethod
    def _kafka_arguments():
        return '-t {} --workernode-data-disks-per-node {}'.format('kafka', '4')

    @staticmethod
    def _rest_proxy_arguments():
        return '--kafka-management-node-size {} --kafka-client-group-id {} --kafka-client-group-name {} -v 4.0 ' \
               '--component-version {} --location {}' \
            .format('Standard_D4_v2', '7bef90fa-0aa3-4bb4-b4d2-2ae7c14cfe41', 'KafakaRestProperties', 'kafka=2.1',
                    '"South Central US"')

    @staticmethod
    def _optional_data_disk_arguments():
        return '--workernode-data-disk-storage-account-type {} --workernode-data-disk-size {}' \
            .format('Standard_LRS', '1023')

    @staticmethod
    def _component_version_arguments():
        return '-t {} --component-version {} --version {}'.format('spark', 'spark=2.4', '4.0')

    @staticmethod
    def _with_cluster_config():
        return '--cluster-configurations {}'.format(r'{{\"gateway\":{{\"restAuthCredential.username\":\"admin\"}}}}')

    @staticmethod
    def _with_explicit_ssh_creds():
        return '--ssh-user {} --ssh-password {}'.format('sshuser', 'Password1!')

    @staticmethod
    def _with_minimal_tls_version(tls_version):
        return '--minimal-tls-version {}'.format(tls_version)

    @staticmethod
    def _with_encryption_in_transit():
        return '--encryption-in-transit true'

    @staticmethod
    def _with_virtual_netowrk_profile(subnet_name):
        return '--subnet {}'.format(subnet_name)

    @staticmethod
    def _with_load_based_autoscale():
        return '--version 4.0 --autoscale-type Load --autoscale-min-workernode-count 4 --autoscale-max-workernode-count 5'

    @staticmethod
    def _with_schedule_based_autoscale():
        return '--version 4.0 --autoscale-type Schedule --timezone "China Standard Time" --days Monday --time "09:00"' \
               ' --autoscale-workernode-count 5'

    @staticmethod
    def _with_encryption_at_host():
        return '--workernode-size Standard_DS14_V2 --headnode-size Standard_DS14_V2 ' \
               '--zookeepernode-size Standard_DS14_V2 --encryption-at-host true'

    @staticmethod
    def _with_private_link_configurations(private_link_configuration_file):
        return '--version 4.0 -l southcentralus ' \
               '--subnet /subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg/providers' \
               '/Microsoft.Network/virtualNetworks/testvnet/subnets/default ' \
               '--resource-provider-connection Outbound --enable-private-link --private-link-configurations @"{}"'\
               .format(private_link_configuration_file)

    @staticmethod
    def _with_availability_zones(custome_all_metastores_file):
        return '--version 4.0 -l southcentralus ' \
               '--subnet /subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg/providers/Microsoft.Network/virtualNetworks/vnetforcreatcluster/subnets/default ' \
               '--zones 1 --cluster-configurations @"{}"'\
               .format(custome_all_metastores_file)

    @staticmethod
    def _with_compute_isolation():
        return '--version 3.6 -l southcentralus ' \
               '--enable-compute-isolation --host-sku ESv3-Type2 ' \
               '--workernode-size Standard_E8S_V3 --headnode-size Standard_E8S_V3'
