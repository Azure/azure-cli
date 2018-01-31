# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from __future__ import print_function

import os
import time
from azure.cli.testsdk import (
    ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer, LiveScenarioTest)

try:
    import unittest.mock as mock
except ImportError:
    import mock

from azure.cli.testsdk import JMESPathCheck, JMESPathCheckExists

NODE_STARTUP_TIME = 10 * 60  # Compute node should start in 10 mins after cluster creation.
CLUSTER_RESIZE_TIME = 20 * 60  # Cluster should resize in 20 mins after job submitted/completed.


def _data_file(filename):
    filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', filename)
    return filepath.replace('\\', '\\\\')


class BatchAIEndToEndScenariosTest(ScenarioTest):
    @ResourceGroupPreparer(location='eastus')
    @StorageAccountPreparer(location='eastus')
    def test_batchai_manual_scale_scenario(self, resource_group, storage_account):

        # Typical usage scenario for regular (not auto scale) cluster.
        # 1. Create a compute cluster
        # 2. Execute some jobs on the cluster
        # 3. Resize the compute cluster to 0
        # 4. Resize the compute cluster to have some nodes
        # 5. Execute more jobs and examine execution results
        # 6. Delete the cluster
        # 7. Delete the jobs

        self._configure_environment(resource_group, storage_account)
        # Create a file share 'share' to be mounted on the cluster
        self.cmd('az storage share create -n share')
        # Create a cluster
        self.cmd('batchai cluster create -n cluster -g {0} -c {1}'.format(
            resource_group, _data_file('cluster_with_azure_files.json')),
            checks=[
                JMESPathCheck('name', 'cluster'),
                JMESPathCheck('allocationState', 'resizing'),
                JMESPathCheck('location', 'eastus'),
                JMESPathCheck('scaleSettings.manual.targetNodeCount', 1),
                JMESPathCheck('vmSize', 'STANDARD_D1'),
                JMESPathCheck('nodeSetup.mountVolumes.azureFileShares[0].accountName', storage_account),
                JMESPathCheck('nodeSetup.mountVolumes.azureFileShares[0].azureFileUrl',
                              'https://{0}.file.core.windows.net/share'.format(storage_account)),
                JMESPathCheck('nodeSetup.mountVolumes.azureFileShares[0].credentialsInfo.accountKey', None),
                JMESPathCheck('userAccountSettings.adminUserName', 'DemoUser'),
                JMESPathCheck('userAccountSettings.adminUserPassword', None)])
        # Create the first job
        self.cmd('batchai job create -n job --cluster-name cluster -g {0} -c {1}'.format(
            resource_group, _data_file('custom_toolkit_job.json')),
            checks=[
                JMESPathCheck('name', 'job'),
                JMESPathCheck('customToolkitSettings.commandLine',
                              'echo hi | tee $AZ_BATCHAI_OUTPUT_OUTPUT/result.txt'),
                JMESPathCheck('executionState', 'queued')])

        # Wait for the cluster to be allocated and job completed
        time.sleep(NODE_STARTUP_TIME)

        # The job must succeed by this time
        self.cmd('batchai job show -n job -g {0}'.format(resource_group), checks=[
            JMESPathCheck('name', 'job'),
            JMESPathCheck('customToolkitSettings.commandLine', 'echo hi | tee $AZ_BATCHAI_OUTPUT_OUTPUT/result.txt'),
            JMESPathCheck('executionState', 'succeeded'),
            JMESPathCheck('executionInfo.exitCode', 0),
            JMESPathCheck('executionInfo.errors', None),
        ])

        # Check the job's standard output: stdout.txt with length equal 3 ("hi\n"), stderr.txt
        self.cmd('batchai job list-files -n job -g {0} -d=stdouterr'.format(resource_group), checks=[
            JMESPathCheck("[].name | sort(@)", ['stderr.txt', 'stdout.txt']),
            JMESPathCheck("[?name == 'stdout.txt'].contentLength", [3]),
            JMESPathCheck("[?name == 'stderr.txt'].contentLength", [0]),
            JMESPathCheckExists("[0].downloadUrl"),
            JMESPathCheckExists("[1].downloadUrl"),
        ])

        # Check the job's output directory
        self.cmd('batchai job list-files -n job -g {0} -d=OUTPUT'.format(resource_group), checks=[
            JMESPathCheck("[].name | sort(@)", ['result.txt']),
            JMESPathCheck("[0].contentLength", 3),  # hi/n
            JMESPathCheckExists("[0].downloadUrl")
        ])

        # Resize the cluster to 0 nodes
        self.cmd('batchai cluster resize -n cluster -g {0} --target 0'.format(resource_group))
        time.sleep(NODE_STARTUP_TIME)

        # Cluster must be resized by this time
        self.cmd('batchai cluster show -n cluster -g {0}'.format(resource_group), checks=[
            JMESPathCheck('name', 'cluster'),
            JMESPathCheck('currentNodeCount', 0),
            JMESPathCheck('scaleSettings.manual.targetNodeCount', 0)
        ])

        # Resize the cluster to execute another job
        self.cmd('batchai cluster resize -n cluster -g {0} --target 1'.format(resource_group))

        # Create another job
        self.cmd('batchai job create -n job2 --cluster-name cluster -g {0} -c {1}'.format(
            resource_group, _data_file('custom_toolkit_job.json')))

        # Wait for the cluster to finish resizing and job execution
        time.sleep(NODE_STARTUP_TIME)

        # The job must succeed by this time
        self.cmd('batchai job show -n job2 -g {0}'.format(resource_group), checks=[
            JMESPathCheck('name', 'job2'),
            JMESPathCheck('executionState', 'succeeded'),
            JMESPathCheck('executionInfo.exitCode', 0),
            JMESPathCheck('executionInfo.errors', None),
        ])

        # Delete the cluster
        self.cmd('batchai cluster delete -n cluster -g {0} -y'.format(resource_group))
        self.cmd('batchai cluster list -g {0}'.format(resource_group), checks=[JMESPathCheck("length(@)", 0)])

        # Delete the jobs
        self.cmd('batchai job delete -n job -g {0} -y'.format(resource_group))
        self.cmd('batchai job delete -n job2 -g {0} -y'.format(resource_group))
        self.cmd('batchai job list -g {0}'.format(resource_group), checks=[JMESPathCheck("length(@)", 0)])

    @ResourceGroupPreparer(location='eastus')
    @StorageAccountPreparer(location='eastus')
    def test_batchai_auto_scale_scenario(self, resource_group, storage_account):

        # Typical usage scenario for auto scale cluster.
        # 1. Create a compute cluster
        # 2. Submit a job
        # 3. The cluster will auto scale to execute the job
        # 4. Examine the job execution results
        # 5. The cluster will down scale

        self._configure_environment(resource_group, storage_account)
        # Create a file share 'share' to be mounted on the cluster
        self.cmd('az storage share create -n share')

        # Create a cluster
        self.cmd('batchai cluster create -n cluster -g {0} -c {1}'.format(
            resource_group, _data_file('auto_scale_cluster_with_azure_files.json')),
            checks=[
                JMESPathCheck('name', 'cluster'),
                JMESPathCheck('allocationState', 'steady'),
                JMESPathCheck('location', 'eastus'),
                JMESPathCheck('scaleSettings.autoScale.minimumNodeCount', 0),
                JMESPathCheck('scaleSettings.autoScale.maximumNodeCount', 1),
                JMESPathCheck('vmSize', 'STANDARD_D1'),
                JMESPathCheck('nodeSetup.mountVolumes.azureFileShares[0].accountName', storage_account),
                JMESPathCheck('nodeSetup.mountVolumes.azureFileShares[0].azureFileUrl',
                              'https://{0}.file.core.windows.net/share'.format(storage_account)),
                JMESPathCheck('nodeSetup.mountVolumes.azureFileShares[0].credentialsInfo.accountKey', None),
                JMESPathCheck('userAccountSettings.adminUserName', 'DemoUser'),
                JMESPathCheck('userAccountSettings.adminUserPassword', None)])
        # Create the job
        self.cmd('batchai job create -n job --cluster-name cluster -g {0} -c {1}'.format(
            resource_group, _data_file('custom_toolkit_job.json')),
            checks=[
                JMESPathCheck('name', 'job'),
                JMESPathCheck('customToolkitSettings.commandLine',
                              'echo hi | tee $AZ_BATCHAI_OUTPUT_OUTPUT/result.txt'),
                JMESPathCheck('executionState', 'queued')])

        # Wait for the cluster to scale up and job completed
        time.sleep(CLUSTER_RESIZE_TIME)

        # The job must succeed by this time
        self.cmd('batchai job show -n job -g {0}'.format(resource_group), checks=[
            JMESPathCheck('name', 'job'),
            JMESPathCheck('customToolkitSettings.commandLine', 'echo hi | tee $AZ_BATCHAI_OUTPUT_OUTPUT/result.txt'),
            JMESPathCheck('executionState', 'succeeded'),
            JMESPathCheck('executionInfo.exitCode', 0),
            JMESPathCheck('executionInfo.errors', None),
        ])

        # Give cluster a time do down scale
        time.sleep(CLUSTER_RESIZE_TIME)

        # By this time the cluster should not have any nodes
        self.cmd('batchai cluster show -n cluster -g {0}'.format(resource_group),
                 checks=JMESPathCheck('currentNodeCount', 0))

    def _configure_environment(self, resource_group, storage_account):

        # Configure storage account related environment variables.
        account_key = self.cmd('storage account keys list -n {} -g {} --query "[0].value" -otsv'.format(
            storage_account, resource_group)).output[:-1]
        self.set_env('AZURE_STORAGE_ACCOUNT', storage_account)
        self.set_env('AZURE_STORAGE_KEY', account_key)
        self.set_env('AZURE_BATCHAI_STORAGE_ACCOUNT', storage_account)
        self.set_env('AZURE_BATCHAI_STORAGE_KEY', account_key)


# TODO: Convert back to ScenarioTest and re-record when #5164 is addressed.
class BatchAILiveScenariosTests(LiveScenarioTest):

    @ResourceGroupPreparer(location='eastus')
    @StorageAccountPreparer(location='eastus')
    def test_batchai_cluster_with_nfs_and_azure_file_share(self, resource_group, storage_account):

        # Tests creation of a cluster with file server and Azure file share.
        # 1. Create a file server and verify parameters.
        # 2. Create a cluster and verify parameters.
        # 3. Verify that cluster was able to start nodes.
        self._configure_environment(resource_group, storage_account)
        # Create a file share 'share' to be mounted on the cluster
        self.cmd('az storage share create -n share')

        self.cmd('batchai file-server create -n nfs -g {0} -c {1}'.format(
            resource_group, _data_file('file_server.json')),
            checks=[
                JMESPathCheck('name', 'nfs'),
                JMESPathCheck('mountSettings.mountPoint', '/mnt/data'),
                JMESPathCheck('dataDisks.diskCount', 2),
                JMESPathCheck('dataDisks.diskSizeInGb', 10)
        ])
        self.cmd('batchai cluster create -n cluster -g {0} -c {1} --nfs nfs --afs-name share -u alex -k {2}'.format(
            resource_group, _data_file('simple_cluster.json'), _data_file('key.txt')),
            checks=[
                JMESPathCheck('nodeSetup.mountVolumes.azureFileShares[0].accountName', storage_account),
                JMESPathCheck('nodeSetup.mountVolumes.azureFileShares[0].azureFileUrl',
                              'https://{0}.file.core.windows.net/share'.format(storage_account)),
                JMESPathCheck('nodeSetup.mountVolumes.azureFileShares[0].relativeMountPath', 'afs'),
                JMESPathCheck('nodeSetup.mountVolumes.azureFileShares[0].credentialsInfo.accountKey', None),
                JMESPathCheck('userAccountSettings.adminUserName', 'alex'),
                JMESPathCheck('userAccountSettings.adminUserPassword', None),
                JMESPathCheck('nodeSetup.mountVolumes.fileServers[0].relativeMountPath', 'nfs')
        ])

        # Give file server and cluster to finish preparation.
        time.sleep(NODE_STARTUP_TIME * 2)

        # Check the node in the cluster successfully started - was able to mount nfs and azure filesystem.
        self.cmd('batchai cluster show -n cluster -g {0}'.format(resource_group),
                 checks=[JMESPathCheck('nodeStateCounts.idleNodeCount', 1)])

        # Check the file server reports information about public ip.
        self.cmd('batchai file-server show -n nfs -g {0}'.format(resource_group),
                 checks=[JMESPathCheckExists('mountSettings.fileServerPublicIp')])

    @ResourceGroupPreparer(location='eastus')
    @StorageAccountPreparer(location='eastus')
    def test_batchai_configless_cluster_and_nfs_creation(self, resource_group, storage_account):

        # Test creation of a cluster and nfs without configuration files.
        self._configure_environment(resource_group, storage_account)
        self.cmd('az storage share create -n share')
        self.cmd('az batchai file-server create -n nfs -g {0} -l eastus --vm-size STANDARD_D1 --storage-sku '
                 'Standard_LRS --disk-count 2 --disk-size 10 -u alex -p Password_123'.format(resource_group))
        self.cmd('az batchai cluster create -n cluster -g {0} -l eastus --afs-name share --nfs nfs '
                 '-i UbuntuLTS --vm-size STANDARD_D1 --min 1 --max 1 -u alex -p Password_123'.format(resource_group),
                 checks=[
                     JMESPathCheck('nodeSetup.mountVolumes.azureFileShares[0].accountName', storage_account),
                     JMESPathCheck('nodeSetup.mountVolumes.azureFileShares[0].azureFileUrl',
                                   'https://{0}.file.core.windows.net/share'.format(storage_account)),
                     JMESPathCheck('nodeSetup.mountVolumes.azureFileShares[0].relativeMountPath', 'afs'),
                     JMESPathCheck('nodeSetup.mountVolumes.azureFileShares[0].credentialsInfo.accountKey', None),
                     JMESPathCheck('userAccountSettings.adminUserName', 'alex'),
                     JMESPathCheck('userAccountSettings.adminUserPassword', None),
                     JMESPathCheck('nodeSetup.mountVolumes.fileServers[0].relativeMountPath', 'nfs')])

        # Give file server and cluster to finish preparation.
        time.sleep(NODE_STARTUP_TIME * 2)

        # Check the node in the cluster successfully started - was able to mount nfs and azure filesystem.
        self.cmd('batchai cluster show -n cluster -g {0}'.format(resource_group),
                 checks=[JMESPathCheck('nodeStateCounts.idleNodeCount', 1)])

        # Check the file server reports information about public ip.
        self.cmd('batchai file-server show -n nfs -g {0}'.format(resource_group),
                 checks=[JMESPathCheckExists('mountSettings.fileServerPublicIp')])

    def _configure_environment(self, resource_group, storage_account):

        # Configure storage account related environment variables.
        account_key = self.cmd('storage account keys list -n {} -g {} --query "[0].value" -otsv'.format(
            storage_account, resource_group)).output[:-1]
        self.set_env('AZURE_STORAGE_ACCOUNT', storage_account)
        self.set_env('AZURE_STORAGE_KEY', account_key)
        self.set_env('AZURE_BATCHAI_STORAGE_ACCOUNT', storage_account)
        self.set_env('AZURE_BATCHAI_STORAGE_KEY', account_key)
