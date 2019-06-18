# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer


class HDInsightClusterTests(ScenarioTest):
    location = 'eastus2'

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

        resize_cluster_format = 'az hdinsight resize -n {cluster} -g {rg} --target-instance-count 2'
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
    def test_hdinsight_cluster_rserver(self, storage_account_info):
        self._create_hdinsight_cluster(
            HDInsightClusterTests._wasb_arguments(storage_account_info),
            HDInsightClusterTests._rserver_arguments()
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
        self.cmd('az hdinsight application create -g {rg} -n {cluster} --application-name {app} '
                 '--script-uri {script_uri} --script-action-name {script_action} --script-parameters {script_params}')
        self.cmd('az hdinsight application wait --created -n {cluster} -g {rg} --application-name {app}')

        # list all applications
        self.cmd('az hdinsight application list -g {rg} -n {cluster}', checks=[
            self.check('type(@)', 'array'),
            self.check('length(@)', 1)
        ])

        # get the specific application
        self.cmd('az hdinsight application show -g {rg} -n {cluster} --application-name {app}', checks=[
            self.check('name', '{app}'),
            self.check('properties.provisioningState', 'Succeeded'),
            self.check('properties.applicationState', 'Running')
        ])

        # delete the specific application
        self.cmd('az hdinsight application delete -g {rg} -n {cluster} --application-name {app} --yes')

        # list applications and validate it is gone.
        self.cmd('az hdinsight application list -g {rg} -n {cluster}', checks=[
            self.check('type(@)', 'array'),
            self.check('length(@)', 0)
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
    def test_hdinsight_oms(self, storage_account_info):
        self.kwargs.update({
            'oms_workspace_id': '1d364e89-bb71-4503-aa3d-a23535aea7bd'
        })

        self._create_hdinsight_cluster(
            HDInsightClusterTests._wasb_arguments(storage_account_info),
            HDInsightClusterTests._with_explicit_ssh_creds()
        )

        # get OMS status
        self.cmd('az hdinsight oms show -g {rg} -n {cluster}', checks=[
            self.check('clusterMonitoringEnabled', False),
            self.check('workspaceId', None)
        ])

        # enable OMS
        self.cmd(
            'az hdinsight oms enable -g {rg} -n {cluster} --workspace-id {oms_workspace_id}')

        # get OMS status
        self.cmd('az hdinsight oms show -g {rg} -n {cluster}', checks=[
            self.check('clusterMonitoringEnabled', True),
            self.check('workspaceId', '{oms_workspace_id}')
        ])

        # disable OMS
        self.cmd('az hdinsight oms disable -g {rg} -n {cluster}')

        # get OMS status
        self.cmd('az hdinsight oms show -g {rg} -n {cluster}', checks=[
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
        self.cmd('az hdinsight script-action execute -g {rg} -n {cluster} '
                 '--script-action-name {script_action} --script-uri {script_uri} --roles {head_node},{worker_node} --persist-on-success')

        # list script actions and validate script is persisted.
        roles = [self.kwargs['head_node'], self.kwargs['worker_node']]
        self.cmd('az hdinsight script-action list -g {rg} -n {cluster} --persisted', checks=[
            self.check('type(@)', 'array'),
            self.check('length(@)', 1),
            self.check('[0].name', '{script_action}'),
            self.check('[0].uri', '{script_uri}'),
            self.check('[0].roles', roles)
        ])

        # delete script action.
        self.cmd('az hdinsight script-action delete -g {rg} -n {cluster} --script-action-name {script_action}')

        # list script actions and validate script is deleted.
        self.cmd('az hdinsight script-action list -g {rg} -n {cluster} --persisted', checks=[
            self.check('type(@)', 'array'),
            self.check('length(@)', 0)
        ])

        # list script action history and validate script appears there.
        script_actions = self.cmd('az hdinsight script-action list -g {rg} -n {cluster}', checks=[
            self.check('type(@)', 'array'),
            self.check('length(@)', 1),
            self.check('[0].name', '{script_action}'),
            self.check('[0].uri', '{script_uri}'),
            self.check('[0].roles', roles),
            self.check('[0].status', 'Succeeded')
        ]).get_output_in_json()

        # get the script action by ID and validate it's the same action.
        self.kwargs['script_execution_id'] = str(script_actions[0]['scriptExecutionId'])
        script_actions = self.cmd('az hdinsight script-action show -g {rg} -n {cluster} '
                                  '--script-execution-id {script_execution_id}',
                                  checks=[
                                      self.check('name', '{script_action}')
                                  ])

        # execute script actions, but don't persist on success.
        self.cmd('az hdinsight script-action execute -g {rg} -n {cluster} '
                 '--script-action-name {script_action_1} --script-uri {script_uri} --roles {head_node},{worker_node}')

        # list script action history and validate the new script also appears.
        script_actions = self.cmd('az hdinsight script-action list -g {rg} -n {cluster}', checks=[
            self.check('type(@)', 'array'),
            self.check('length(@)', 2),
            self.check('[0].name', '{script_action_1}'),
            self.check("[0].uri", '{script_uri}'),
            self.check("[0].status", 'Succeeded')
        ]).get_output_in_json()

        # promote non-persisted script.
        self.kwargs['script_execution_id'] = str(script_actions[0]['scriptExecutionId'])
        script_actions = self.cmd('az hdinsight script-action promote -g {rg} -n {cluster} '
                                  '--script-execution-id {script_execution_id}')

        # list script action list and validate the promoted script is the only one there.
        self.cmd('az hdinsight script-action list -g {rg} -n {cluster} --persisted', checks=[
            self.check('type(@)', 'array'),
            self.check('length(@)', 1),
            self.check('[0].name', '{script_action_1}'),
            self.check('[0].uri', '{script_uri}'),
            self.check('[0].roles', roles),
            self.check('[0].status', None)
        ])

        # list script action history and validate both scripts are there.
        script_actions = self.cmd('az hdinsight script-action list -g {rg} -n {cluster}', checks=[
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

    def _create_hdinsight_cluster(self, *additional_create_arguments):
        self.kwargs.update({
            'loc': self.location,
            'cluster': self.create_random_name(prefix='hdicli-', length=16),
            'http_password': 'Password1!',
            'cluster_type': 'spark'
        })

        create_cluster_format = 'az hdinsight create -n {cluster} -g {rg} -l {loc} -p {http_password} -t {cluster_type} ' \
                                + ' '.join(additional_create_arguments)
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
        container_args = ' --storage-default-container {}'.format('default') if specify_container else ""

        return '--storage-account {}{}{}'\
            .format(storage_account_name, key_args, container_args)

    @staticmethod
    def _kafka_arguments():
        return '-t {} --workernode-data-disks-per-node {}'.format('kafka', '4')

    @staticmethod
    def _optional_data_disk_arguments():
        return '--workernode-data-disk-storage-account-type {} --workernode-data-disk-size {}'\
               .format('Standard_LRS', '1023')

    @staticmethod
    def _rserver_arguments():
        return '-t {} --edgenode-size {} -v 3.6'.format('rserver', 'large')

    @staticmethod
    def _component_version_arguments():
        return '-t {} --component-version {}'.format('spark', 'spark=2.2')

    @staticmethod
    def _with_cluster_config():
        return '--cluster-configurations {}'.format(r'{{\"gateway\":{{\"restAuthCredential.username\":\"admin\"}}}}')

    @staticmethod
    def _with_explicit_ssh_creds():
        return '--ssh-user {} --ssh-password {}'.format('sshuser', 'Password1!')
