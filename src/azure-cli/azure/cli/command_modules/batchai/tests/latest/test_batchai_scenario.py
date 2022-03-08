# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import time
import uuid
from contextlib import contextmanager

import os
from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer

from unittest import mock

from azure.cli.testsdk import JMESPathCheck, JMESPathCheckExists, StringContainCheck
from azure.cli.testsdk.scenario_tests import AllowLargeResponse

NODE_STARTUP_TIME = 10 * 60  # Compute node should start in 10 mins after cluster creation.
CLUSTER_RESIZE_TIME = 20 * 60  # Cluster should resize in 20 mins after job submitted/completed.
LOCATION_FOR_SCENARIO_TESTS = 'eastus'
PASSWORD = str(uuid.uuid4())


def _data_file(filename):
    filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', filename)
    return filepath.replace('\\', '\\\\')


class BatchAIEndToEndScenariosTest(ScenarioTest):
    @ResourceGroupPreparer(location=LOCATION_FOR_SCENARIO_TESTS)
    @StorageAccountPreparer(location=LOCATION_FOR_SCENARIO_TESTS)
    def test_batchai_manual_scale_scenario(self, resource_group, storage_account_info):
        # Typical usage scenario for regular (not auto scale) cluster.
        # 1. Create a compute cluster
        # 2. Execute some jobs on the cluster
        # 3. Resize the compute cluster to 0
        # 4. Resize the compute cluster to have some nodes
        # 5. Execute more jobs and examine execution results
        # 6. Delete the cluster
        # 7. Delete the jobs
        with self._given_configured_environment(resource_group, storage_account_info):
            storage_account, account_key = storage_account_info
            # Create a file share 'share' to be mounted on the cluster
            self.cmd('az storage share create -n share')
            # Create a workspace
            self.cmd('az batchai workspace create -g {0} -n workspace'.format(resource_group),
                     checks=[JMESPathCheck('name', 'workspace')])
            self.cmd('az batchai workspace list -g {0}'.format(resource_group), checks=[JMESPathCheck("length(@)", 1)])
            # Create a cluster
            self.cmd('az batchai cluster create -g {0} -w workspace -n cluster -f "{1}"'.format(
                resource_group, _data_file('cluster_with_azure_files.json')),
                checks=[
                    JMESPathCheck('name', 'cluster'),
                    JMESPathCheck('allocationState', 'resizing'),
                    JMESPathCheck('scaleSettings.manual.targetNodeCount', 1),
                    JMESPathCheck('vmSize', 'STANDARD_D1'),
                    JMESPathCheck('nodeSetup.mountVolumes.azureFileShares[0].accountName', storage_account),
                    JMESPathCheck('nodeSetup.mountVolumes.azureFileShares[0].azureFileUrl',
                                  'https://{0}.file.core.windows.net/share'.format(storage_account)),
                    JMESPathCheck('nodeSetup.mountVolumes.azureFileShares[0].credentialsInfo.accountKey', None),
                    JMESPathCheck('userAccountSettings.adminUserName', 'DemoUser'),
                    JMESPathCheck('userAccountSettings.adminUserPassword', None)])
            # Create an experiment
            self.cmd('az batchai experiment create -g {0} -w workspace -n experiment'.format(resource_group),
                     checks=[JMESPathCheck('name', 'experiment')])
            self.cmd('az batchai experiment list -g {0} -w workspace'.format(resource_group),
                     checks=[JMESPathCheck("length(@)", 1)])
            # Create the first job
            self.cmd('az batchai job create -c cluster -g {0} -w workspace -e experiment -n job -f "{1}"'.format(
                resource_group, _data_file('custom_toolkit_job.json')),
                checks=[
                    JMESPathCheck('name', 'job'),
                    JMESPathCheck('customToolkitSettings.commandLine',
                                  'echo hi | tee $AZ_BATCHAI_OUTPUT_OUTPUT/result.txt'),
                    JMESPathCheck('executionState', 'queued')])

            # Wait for the cluster to be allocated and job completed
            self.cmd('az batchai job wait -g {0} -w workspace -e experiment -n job'.format(resource_group))

            # Check the job's results
            self.cmd('az batchai job show -g {0} -w workspace -e experiment -n job'.format(resource_group), checks=[
                JMESPathCheck('name', 'job'),
                JMESPathCheck(
                    'customToolkitSettings.commandLine', 'echo hi | tee $AZ_BATCHAI_OUTPUT_OUTPUT/result.txt'),
                JMESPathCheck('executionState', 'succeeded'),
                JMESPathCheck('executionInfo.exitCode', 0),
                JMESPathCheck('executionInfo.errors', None),
            ])

            # Check the job's standard output: stdout.txt with length equal 3 ("hi\n"), stderr.txt
            self.cmd('az batchai job file list -g {0} -w workspace -e experiment -j job -d stdouterr'.format(
                resource_group), checks=[
                    JMESPathCheck("[].name | contains(@, 'execution.log')", True),
                    JMESPathCheck("[].name | contains(@, 'stderr.txt')", True),
                    JMESPathCheck("[].name | contains(@, 'stdout.txt')", True),
                    JMESPathCheck("[?name == 'stdout.txt'].contentLength", [3]),
                    JMESPathCheckExists("[0].downloadUrl"),
                    JMESPathCheckExists("[1].downloadUrl"),
            ])

            # Check the job's output directory
            self.cmd('az batchai job file list -g {0} -w workspace -e experiment -j job -d=OUTPUT'.format(
                resource_group),
                checks=[
                    JMESPathCheck("[].name | sort(@)", ['result.txt']),
                    JMESPathCheck("[0].contentLength", 3),  # hi/n
                    JMESPathCheckExists("[0].downloadUrl")
            ])

            # Resize the cluster to 0 nodes
            self.cmd('az batchai cluster resize -g {0} -w workspace -n cluster -t 0'.format(resource_group))
            time.sleep(NODE_STARTUP_TIME)

            # Cluster must be resized by this time
            self.cmd('az batchai cluster show -g {0} -w workspace -n cluster'.format(resource_group),
                     checks=[
                         JMESPathCheck('name', 'cluster'),
                         JMESPathCheck('currentNodeCount', 0),
                         JMESPathCheck('scaleSettings.manual.targetNodeCount', 0)
            ])

            # Resize the cluster to execute another job
            self.cmd('az batchai cluster resize -g {0} -w workspace -n cluster -t 1'.format(resource_group))

            # Create another job
            self.cmd('az batchai job create -c cluster -g {0} -w workspace -e experiment -n job2 -f "{1}"'.format(
                resource_group, _data_file('custom_toolkit_job.json')))

            # Wait for the cluster to finish resizing and job execution
            self.cmd('az batchai job wait -g {0} -w workspace -e experiment -n job2'.format(resource_group))

            # The job must succeed by this time
            self.cmd('az batchai job show -g {0} -w workspace -e experiment -n job2'.format(resource_group), checks=[
                JMESPathCheck('name', 'job2'),
                JMESPathCheck('executionState', 'succeeded'),
                JMESPathCheck('executionInfo.exitCode', 0),
                JMESPathCheck('executionInfo.errors', None),
            ])

            # Delete the cluster
            self.cmd('batchai cluster delete -g {0} -w workspace -n cluster -y'.format(resource_group))
            self.cmd('batchai cluster list -g {0} -w workspace'.format(resource_group),
                     checks=[JMESPathCheck("length(@)", 0)])

            # Delete the jobs
            self.cmd('az batchai job delete -g {0} -w workspace -e experiment -n job -y'.format(resource_group))
            self.cmd('az batchai job delete -g {0} -w workspace -e experiment -n job2 -y'.format(resource_group))
            self.cmd('az batchai job list -g {0} -w workspace -e experiment'.format(resource_group),
                     checks=[JMESPathCheck("length(@)", 0)])

    @ResourceGroupPreparer(location=LOCATION_FOR_SCENARIO_TESTS)
    @StorageAccountPreparer(location=LOCATION_FOR_SCENARIO_TESTS)
    def test_batchai_auto_scale_scenario(self, resource_group, storage_account_info):
        # Typical usage scenario for auto scale cluster.
        # 1. Create a compute cluster
        # 2. Submit a job
        # 3. The cluster will auto scale to execute the job
        # 4. Examine the job execution results
        # 5. The cluster will down scale
        with self._given_configured_environment(resource_group, storage_account_info):
            storage_account, account_key = storage_account_info
            # Create a file share 'share' to be mounted on the cluster
            self.cmd('az storage share create -n share')
            # Create a workspace
            self.cmd('az batchai workspace create -g {0} -n workspace'.format(resource_group),
                     checks=[JMESPathCheck('name', 'workspace')])
            # Create a cluster
            self.cmd('az batchai cluster create -g {0} -w workspace -n cluster -f "{1}"'.format(
                resource_group, _data_file('auto_scale_cluster_with_azure_files.json')),
                checks=[
                    JMESPathCheck('name', 'cluster'),
                    JMESPathCheck('scaleSettings.autoScale.minimumNodeCount', 0),
                    JMESPathCheck('scaleSettings.autoScale.maximumNodeCount', 1),
                    JMESPathCheck('vmSize', 'STANDARD_D1'),
                    JMESPathCheck('nodeSetup.mountVolumes.azureFileShares[0].accountName', storage_account),
                    JMESPathCheck('nodeSetup.mountVolumes.azureFileShares[0].azureFileUrl',
                                  'https://{0}.file.core.windows.net/share'.format(storage_account)),
                    JMESPathCheck('nodeSetup.mountVolumes.azureFileShares[0].credentialsInfo.accountKey', None),
                    JMESPathCheck('userAccountSettings.adminUserName', 'DemoUser'),
                    JMESPathCheck('userAccountSettings.adminUserPassword', None)])
            # Create an experiment
            self.cmd('az batchai experiment create -g {0} -w workspace -n experiment'.format(resource_group),
                     checks=[JMESPathCheck('name', 'experiment')])
            # Create the job
            self.cmd('az batchai job create -c cluster -g {0} -w workspace -e experiment -n job -f "{1}"'.format(
                resource_group, _data_file('custom_toolkit_job.json')),
                checks=[
                    JMESPathCheck('name', 'job'),
                    JMESPathCheck('customToolkitSettings.commandLine',
                                  'echo hi | tee $AZ_BATCHAI_OUTPUT_OUTPUT/result.txt'),
                    JMESPathCheck('executionState', 'queued')])

            # Wait for the cluster to scale up and job completed
            self.cmd('az batchai job wait -g {0} -w workspace -e experiment -n job'.format(resource_group))

            # The job must succeed by this time
            self.cmd('az batchai job show -g {0} -w workspace -e experiment -n job'.format(resource_group), checks=[
                JMESPathCheck('name', 'job'),
                JMESPathCheck(
                    'customToolkitSettings.commandLine', 'echo hi | tee $AZ_BATCHAI_OUTPUT_OUTPUT/result.txt'),
                JMESPathCheck('executionState', 'succeeded'),
                JMESPathCheck('executionInfo.exitCode', 0),
                JMESPathCheck('executionInfo.errors', None),
            ])

            # Give cluster a time do down scale
            time.sleep(CLUSTER_RESIZE_TIME)

            # By this time the cluster should not have any nodes
            self.cmd('az batchai cluster show -g {0} -w workspace -n cluster'.format(resource_group),
                     checks=JMESPathCheck('currentNodeCount', 0))

    @ResourceGroupPreparer(location=LOCATION_FOR_SCENARIO_TESTS)
    @StorageAccountPreparer(location=LOCATION_FOR_SCENARIO_TESTS)
    def test_batchai_cluster_with_file_systems(self, resource_group, storage_account_info):
        # Tests creation of a cluster with mounted file systems defined in config.
        # 1. Create an Azure File Share and Azure Blob Container to mount on the cluster.
        # 2. Create a cluster and verify parameters.
        # 3. Verify that cluster was able to start nodes.
        with self._given_configured_environment(resource_group, storage_account_info):
            storage_account, account_key = storage_account_info
            # Create a file share 'share' and blob container 'container' to be mounted on cluster nodes.
            self.cmd('az storage share create -n share')
            self.cmd('az storage container create -n container')
            self.cmd('az batchai workspace create -g {0} -n workspace'.format(resource_group),
                     checks=[JMESPathCheck('name', 'workspace')])
            self.cmd(
                'az batchai cluster create -g {0} -w workspace -n cluster -f "{1}" '
                '--afs-name share --bfs-name container '
                '-u DemoUser -k "{2}"'.format(resource_group, _data_file('simple_cluster.json'), _data_file('key.txt')),
                checks=[
                    JMESPathCheck('nodeSetup.mountVolumes.azureFileShares[0].accountName', storage_account),
                    JMESPathCheck('nodeSetup.mountVolumes.azureFileShares[0].azureFileUrl',
                                  'https://{0}.file.core.windows.net/share'.format(storage_account)),
                    JMESPathCheck('nodeSetup.mountVolumes.azureFileShares[0].relativeMountPath', 'afs'),
                    JMESPathCheck('nodeSetup.mountVolumes.azureFileShares[0].credentialsInfo.accountKey', None),
                    JMESPathCheck('nodeSetup.mountVolumes.azureBlobFileSystems[0].accountName', storage_account),
                    JMESPathCheck('nodeSetup.mountVolumes.azureBlobFileSystems[0].containerName', 'container'),
                    JMESPathCheck('nodeSetup.mountVolumes.azureBlobFileSystems[0].relativeMountPath', 'bfs'),
                    JMESPathCheck('nodeSetup.mountVolumes.azureBlobFileSystems[0].credentialsInfo.accountKey', None),
                    JMESPathCheck('userAccountSettings.adminUserName', 'DemoUser'),
                    JMESPathCheck('userAccountSettings.adminUserPassword', None)])

            # Give file server and cluster to finish preparation.
            time.sleep(NODE_STARTUP_TIME * 2)

            # Check the node in the cluster successfully started - was able to mount nfs and azure filesystem.
            self.cmd('az batchai cluster show -g {0} -w workspace -n cluster'.format(resource_group),
                     checks=[JMESPathCheck('nodeStateCounts.idleNodeCount', 1)])

    @ResourceGroupPreparer(location=LOCATION_FOR_SCENARIO_TESTS)
    @StorageAccountPreparer(location=LOCATION_FOR_SCENARIO_TESTS)
    def test_batchai_config_less_cluster_with_file_systems(self, resource_group, storage_account_info):
        # Test creation of a cluster with mount file systems defined via command line.
        with self._given_configured_environment(resource_group, storage_account_info):
            storage_account, account_key = storage_account_info
            self.cmd('az storage share create -n share')
            self.cmd('az storage container create -n container')
            self.cmd('az batchai workspace create -g {0} -n workspace'.format(resource_group))
            self.cmd(
                'az batchai cluster create -g {0} -w workspace -n cluster '
                '-i UbuntuLTS --vm-size STANDARD_D1 --min 1 --max 1 -u DemoUser -k "{1}" '
                '--afs-name share --bfs-name container'.format(
                    resource_group, _data_file('key.txt')),
                checks=[
                    JMESPathCheck('nodeSetup.mountVolumes.azureFileShares[0].accountName', storage_account),
                    JMESPathCheck('nodeSetup.mountVolumes.azureFileShares[0].azureFileUrl',
                                  'https://{0}.file.core.windows.net/share'.format(storage_account)),
                    JMESPathCheck('nodeSetup.mountVolumes.azureFileShares[0].relativeMountPath', 'afs'),
                    JMESPathCheck('nodeSetup.mountVolumes.azureFileShares[0].credentialsInfo.accountKey', None),
                    JMESPathCheck('nodeSetup.mountVolumes.azureBlobFileSystems[0].accountName', storage_account),
                    JMESPathCheck('nodeSetup.mountVolumes.azureBlobFileSystems[0].containerName', 'container'),
                    JMESPathCheck('nodeSetup.mountVolumes.azureBlobFileSystems[0].relativeMountPath', 'bfs'),
                    JMESPathCheck('nodeSetup.mountVolumes.azureBlobFileSystems[0].credentialsInfo.accountKey', None),
                    JMESPathCheck('userAccountSettings.adminUserName', 'DemoUser'),
                    JMESPathCheck('userAccountSettings.adminUserPassword', None)])

            # Give file server and cluster to finish preparation.
            time.sleep(NODE_STARTUP_TIME * 2)

            # Check the node in the cluster successfully started - was able to mount nfs and azure filesystem.
            self.cmd('az batchai cluster show -g {0} -w workspace -n cluster'.format(resource_group),
                     checks=[JMESPathCheck('nodeStateCounts.idleNodeCount', 1)])

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=LOCATION_FOR_SCENARIO_TESTS)
    @StorageAccountPreparer(name_prefix='bai', location=LOCATION_FOR_SCENARIO_TESTS)
    def test_batchai_cluster_with_auto_storage(self, resource_group, storage_account):
        # Test creation of a cluster with auto-storage account.
        with mock.patch('azure.cli.command_modules.batchai.custom._get_auto_storage_resource_group') as p:
            p.return_value = resource_group
            self.cmd('az batchai workspace create -g {0} -n workspace'.format(resource_group))
            self.cmd(
                'az batchai cluster create -g {0} -w workspace -n cluster '
                '-i UbuntuLTS --vm-size STANDARD_D1 -t 0 -u DemoUser -k "{1}" '
                '--use-auto-storage'.format(
                    resource_group, _data_file('key.txt')),
                checks=[
                    JMESPathCheck('nodeSetup.mountVolumes.azureFileShares[0].accountName', storage_account),
                    JMESPathCheck('nodeSetup.mountVolumes.azureFileShares[0].azureFileUrl',
                                  'https://{0}.file.core.windows.net/batchaishare'.format(storage_account)),
                    JMESPathCheck('nodeSetup.mountVolumes.azureFileShares[0].relativeMountPath', 'autoafs'),
                    JMESPathCheck('nodeSetup.mountVolumes.azureBlobFileSystems[0].accountName', storage_account),
                    JMESPathCheck('nodeSetup.mountVolumes.azureBlobFileSystems[0].containerName', 'batchaicontainer'),
                    JMESPathCheck('nodeSetup.mountVolumes.azureBlobFileSystems[0].relativeMountPath', 'autobfs')])

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=LOCATION_FOR_SCENARIO_TESTS)
    @StorageAccountPreparer(name_prefix='bai', location=LOCATION_FOR_SCENARIO_TESTS)
    def test_batchai_cluster_with_setup_command(self, resource_group, storage_account):
        # Test creation of a cluster with auto-storage account and setup task.
        with mock.patch('azure.cli.command_modules.batchai.custom._get_auto_storage_resource_group') as p:
            p.return_value = resource_group
            self.cmd('az batchai workspace create -g {0} -n workspace'.format(resource_group))
            self.cmd(
                'az batchai cluster create -n cluster -g {0} -w workspace -s STANDARD_D1 -t 0 -u DemoUser -k "{1}" '
                '--use-auto-storage --setup-task "echo hi" --setup-task-output "$AZ_BATCHAI_MOUNT_ROOT/autoafs"'.format(
                    resource_group, _data_file('key.txt')),
                checks=[
                    JMESPathCheck('nodeSetup.setupTask.commandLine', 'echo hi'),
                    JMESPathCheck('nodeSetup.setupTask.stdOutErrPathPrefix', '$AZ_BATCHAI_MOUNT_ROOT/autoafs'),
                    JMESPathCheck('nodeSetup.mountVolumes.azureFileShares[0].accountName', storage_account),
                    JMESPathCheck('nodeSetup.mountVolumes.azureFileShares[0].azureFileUrl',
                                  'https://{0}.file.core.windows.net/batchaishare'.format(storage_account)),
                    JMESPathCheck('nodeSetup.mountVolumes.azureFileShares[0].relativeMountPath', 'autoafs'),
                    JMESPathCheck('nodeSetup.mountVolumes.azureBlobFileSystems[0].accountName', storage_account),
                    JMESPathCheck('nodeSetup.mountVolumes.azureBlobFileSystems[0].containerName', 'batchaicontainer'),
                    JMESPathCheck('nodeSetup.mountVolumes.azureBlobFileSystems[0].relativeMountPath', 'autobfs')])

    @ResourceGroupPreparer(location=LOCATION_FOR_SCENARIO_TESTS)
    @StorageAccountPreparer(location=LOCATION_FOR_SCENARIO_TESTS)
    def test_batchai_job_level_mounting_scenario(self, resource_group, storage_account_info):
        # Typical usage scenario for regular (not auto scale) cluster.
        # 1. Create a compute cluster.
        # 2. Execute a job with job level filesystems when file systems specified in config file.
        # 3. Check the job succeeded and files are generated.
        # 4. Execute a job with job level filesystems when file systems specified via command line.
        # 5. Check the job succeeded and files are generated.
        with self._given_configured_environment(resource_group, storage_account_info):
            storage_account, account_key = storage_account_info
            # Create a file share 'share' to be mounted on the cluster
            self.cmd('az storage share create -n share')
            self.cmd('az storage container create -n container')
            # Create a workspace
            self.cmd('az batchai workspace create -g {0} -n workspace'.format(resource_group))
            # Create a cluster
            self.cmd('az batchai cluster create -g {0} -w workspace -n cluster -f "{1}" -u DemoUser -k "{2}"'.format(
                resource_group, _data_file('simple_cluster.json'), _data_file('key.txt')))
            # Create an experiment
            self.cmd('az batchai experiment create -g {0} -w workspace -n experiment'.format(resource_group))
            # Submit the job which has mount_volumes in the config file.
            self.cmd('az batchai job create -c cluster -g {0} -w workspace -e experiment -n job -f "{1}"'.format(
                resource_group, _data_file('job_with_file_systems.json')))
            # Wait for the cluster to be allocated and job completed
            self.cmd('az batchai job wait -g {0} -w workspace -e experiment -n job'.format(resource_group))
            # Check the job's results
            self.cmd('az batchai job show -g {0} -w workspace -e experiment -n job'.format(resource_group), checks=[
                JMESPathCheck('name', 'job'),
                JMESPathCheck(
                    'customToolkitSettings.commandLine', 'echo hi | tee $AZ_BATCHAI_OUTPUT_OUTPUT/result.txt'),
                JMESPathCheck('executionState', 'succeeded'),
                # JMESPathCheck(' .exitCode', 0),
                JMESPathCheck('executionInfo.errors', None),
            ])
            # Check the job's standard output: stdout.txt with length equal 3 ("hi\n"), stderr.txt
            self.cmd('az batchai job file list -g {0} -w workspace -e experiment -j job -d stdouterr'.format(
                resource_group), checks=[
                    JMESPathCheck("[].name | contains(@, 'execution.log')", True),
                    JMESPathCheck("[].name | contains(@, 'stderr.txt')", True),
                    JMESPathCheck("[].name | contains(@, 'stdout.txt')", True),
                    JMESPathCheck("[?name == 'stdout.txt'].contentLength", [3]),
                    JMESPathCheckExists("[0].downloadUrl"),
                    JMESPathCheckExists("[1].downloadUrl"),
            ])
            # Check the job's output directory
            self.cmd('az batchai job file list -g {0} -w workspace -e experiment -j job -d OUTPUT'.format(
                resource_group), checks=[
                JMESPathCheck("[].name | contains(@, 'result.txt')", True),
                JMESPathCheck("[0].contentLength", 3),  # hi/n
                JMESPathCheckExists("[0].downloadUrl")
            ])
            # Submit the job specifying Azure File Share and Azure Blob Container via command line args
            self.cmd('az batchai job create -c cluster -g {0} -w workspace -e experiment -n job2 -f "{1}" '
                     '--afs-name share --bfs-name container'.format(resource_group,
                                                                    _data_file('job_referencing_file_systems.json')))
            # Wait for the cluster to be allocated and job completed
            self.cmd('batchai job wait -g {0} -w workspace -e experiment -n job2'.format(resource_group))
            # Check the job's results
            self.cmd('batchai job show -g {0} -w workspace -e experiment -n job2'.format(resource_group), checks=[
                JMESPathCheck('name', 'job2'),
                JMESPathCheck(
                    'customToolkitSettings.commandLine', 'echo hi | tee $AZ_BATCHAI_OUTPUT_OUTPUT/result.txt'),
                JMESPathCheck('executionState', 'succeeded'),
                JMESPathCheck('executionInfo.exitCode', 0),
                JMESPathCheck('executionInfo.errors', None),
            ])
            # Check the job's standard output: stdout.txt with length equal 3 ("hi\n"), stderr.txt
            self.cmd('batchai job file list -g {0} -w workspace -e experiment -j job2 -d stdouterr'.format(
                resource_group), checks=[
                JMESPathCheck("[].name | contains(@, 'execution.log')", True),
                JMESPathCheck("[].name | contains(@, 'stderr.txt')", True),
                JMESPathCheck("[].name | contains(@, 'stdout.txt')", True),
                JMESPathCheck("[?name == 'stdout.txt'].contentLength", [3]),
                JMESPathCheckExists("[0].downloadUrl"),
                JMESPathCheckExists("[1].downloadUrl"),
            ])
            # Check the job's output directory
            self.cmd('batchai job file list -g {0} -w workspace -e experiment -j job2 -d OUTPUT'.format(
                resource_group), checks=[
                JMESPathCheck("[].name | contains(@, 'result.txt')", True),
                JMESPathCheck("[0].contentLength", 3),  # hi/n
                JMESPathCheckExists("[0].downloadUrl")
            ])

    def test_batchai_usages(self):
        # Just check if we can get a usage and it contains info about clusters.
        self.cmd('batchai list-usages -l {0}'.format(LOCATION_FOR_SCENARIO_TESTS), checks=[
            StringContainCheck("Cluster")])
        self.cmd('batchai list-usages -l {0} -o table'.format(LOCATION_FOR_SCENARIO_TESTS), checks=[
            StringContainCheck("Cluster")])

    @contextmanager
    def _given_configured_environment(self, resource_group, storage_account_info):

        # Configure storage account related environment variables.
        storage_account, account_key = storage_account_info
        self.set_env('AZURE_STORAGE_ACCOUNT', storage_account)
        self.set_env('AZURE_STORAGE_KEY', account_key)
        self.set_env('AZURE_BATCHAI_STORAGE_ACCOUNT', storage_account)
        self.set_env('AZURE_BATCHAI_STORAGE_KEY', account_key)
        try:
            yield
        finally:
            self.pop_env('AZURE_STORAGE_ACCOUNT')
            self.pop_env('AZURE_STORAGE_KEY')
            self.pop_env('AZURE_BATCHAI_STORAGE_ACCOUNT')
            self.pop_env('AZURE_BATCHAI_STORAGE_KEY')
