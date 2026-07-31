# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import datetime
import tempfile
import time

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer
from knack.util import CLIError
from .batch_preparers import BatchAccountPreparer, BatchScenarioMixin

from .recording_processors import BatchAccountKeyReplacer, StorageSASReplacer


class BatchDataPlaneScenarioTests(BatchScenarioMixin, ScenarioTest):

    def __init__(self, method_name):
        super().__init__(method_name, recording_processors=[
            BatchAccountKeyReplacer(),
            StorageSASReplacer()
        ])

    def _get_test_data_file(self, filename):
        filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', filename)
        self.assertTrue(os.path.isfile(filepath), 'File {} does not exist.'.format(filepath))
        return filepath

    @ResourceGroupPreparer()
    @BatchAccountPreparer()
    def test_batch_pool_cmd(
            self,
            resource_group,
            batch_account_name):
        endpoint = self.get_account_endpoint(
            batch_account_name,
            resource_group).replace("https://", "")
        key = self.get_account_key(
            batch_account_name,
            resource_group)

        self.kwargs.update({
            'p_id': 'xplatCreatedPool',
            'c_file': self._get_test_data_file('batchCreatePool.json'),
            'u_file': self._get_test_data_file('batchUpdatePool.json'),
            'acc_n': batch_account_name,
            'acc_k': key,
            'acc_u': endpoint
        })
        self.batch_cmd('batch pool create --json-file "{c_file}"')
        result = self.batch_cmd('batch pool create --id pool_image1 --vm-size Standard_DS1_v2 '
                                '--image a:b:c --node-agent-sku-id "batch.node.windows amd64"',
                                expect_failure=True)

        result = self.batch_cmd('batch pool create --id pool_image1 --vm-size Standard_DS1_v2 '
                                '--image /subscriptions/11111111-1111-1111-1111-111111111111'
                                '/resourceGroups/test_rg/providers/Microsoft.Compute/images/custom_image '
                                '--node-agent-sku-id "batch.node.windows amd64"',
                                expect_failure=True)

        result = self.batch_cmd('batch pool create --id pool_image1 --vm-size Standard_DS1_v2 '
                                '--image canonical:ubuntuserver:18.04-lts --node-agent-sku-id "batch.node.ubuntu 18.04" '
                                '--disk-encryption-targets "TemporaryDisk"')

        self.wait_for_pool_steady("pool_image1")

        result = self.batch_cmd('batch pool show --pool-id {p_id}').assert_with_checks([
            self.check('allocationState', 'steady'),
            self.check('id', 'xplatCreatedPool'),
            self.check('startTask.commandLine', "cmd /c echo test"),
            self.check('startTask.userIdentity.autoUser.elevationLevel', "admin")])

        target = result.get_output_in_json()['currentLowPriorityNodes']
        self.batch_cmd('batch pool resize --pool-id {p_id} --target-dedicated-nodes 0 --target-low-priority-nodes 3 --resize-timeout PT0H20M')
        self.batch_cmd('batch pool show --pool-id {p_id}').assert_with_checks([
            self.check('allocationState', 'resizing'),
            self.check('targetLowPriorityNodes', 3),
            self.check('id', 'xplatCreatedPool')])

        self.batch_cmd('batch pool resize --pool-id {p_id} --abort')

        self.wait_for_pool_steady("xplatCreatedPool")

        self.batch_cmd('batch pool node-counts list').assert_with_checks([
            self.check('length(@)', 2),
            self.check('[1].poolId', 'xplatCreatedPool')])

        self.batch_cmd('batch pool show --pool-id {p_id}').assert_with_checks([
            self.check('allocationState', 'steady'),
            self.check('id', 'xplatCreatedPool'),
            self.check('currentLowPriorityNodes', target),
            self.check('targetLowPriorityNodes', 3),
            self.check('metadata', None)])

        # Set a property which will be cleared by the subsequent reset command
        self.batch_cmd('batch pool set --pool-id {p_id} --metadata foo=bar')
        self.batch_cmd('batch pool show --pool-id {p_id}').assert_with_checks([
            self.check('id', 'xplatCreatedPool'),
            self.check('length(metadata)', 1),
            self.check('metadata[0].name', 'foo'),
            self.check('metadata[0].value', 'bar')])

        self.batch_cmd('batch pool reset --pool-id {p_id} --json-file "{u_file}"').assert_with_checks([
            self.check('allocationState', 'steady'),
            self.check('id', 'xplatCreatedPool'),
            self.check('startTask.commandLine', "cmd /c echo updated"),
            self.check('metadata', None)])

        self.batch_cmd('batch pool reset --pool-id {p_id} --start-task-command-line hostname '
                       '--start-task-resource-files hello.txt=https://contoso.net/hello.txt --metadata a=b c=d').assert_with_checks([
                           self.check('allocationState', 'steady'),
                           self.check('id', 'xplatCreatedPool'),
                           self.check('startTask.commandLine', "hostname"),
                           self.check('length(metadata)', 2),
                           self.check('metadata[0].name', 'a'),
                           self.check('metadata[1].value', 'd')])

        # test that deprecated --target-communication for pool reset
        with self.assertRaises(SystemExit):
            self.batch_cmd('batch pool reset --pool-id {p_id} --target-communication classic')

        self.batch_cmd('batch pool delete --pool-id {p_id} --yes')

    @ResourceGroupPreparer()
    @BatchAccountPreparer()
    def test_batch_pool_trustedLaunch_cmd(
            self,
            resource_group,
            batch_account_name):
        endpoint = self.get_account_endpoint(
            batch_account_name,
            resource_group).replace("https://", "")
        key = self.get_account_key(
            batch_account_name,
            resource_group)

        self.kwargs.update({
            'p_id': 'xplatCreatedPool',
            'acc_n': batch_account_name,
            'acc_k': key,
            'acc_u': endpoint
        })

        self.batch_cmd('batch pool create --id {p_id} --vm-size "standard_d2s_v3" '
                        '--image "canonical:ubuntuserver:18.04-lts" '
                        '--node-agent-sku-id "batch.node.ubuntu 18.04" '
                        '--target-dedicated-nodes 2 '
                        '--security-type "TrustedLaunch" '
                        '--encryption-at-host true '
                        '--enable-secure-boot true '
                        '--enable-vtpm true')

        res = self.batch_cmd('batch pool show --pool-id {p_id}').get_output_in_json()

        self.assertTrue(res['virtualMachineConfiguration']['securityProfile']['securityType'])
        self.assertTrue(res['virtualMachineConfiguration']['securityProfile']['encryptionAtHost'])
        self.assertTrue(res['virtualMachineConfiguration']['securityProfile']['uefiSettings']['secureBootEnabled'])
        self.assertTrue(res['virtualMachineConfiguration']['securityProfile']['uefiSettings']['vTpmEnabled'])

        self.batch_cmd('batch pool delete --pool-id {p_id} --yes')

    @ResourceGroupPreparer()
    @BatchAccountPreparer()
    def test_batch_pool_osDisk_cmd(
            self,
            resource_group,
            batch_account_name):
        endpoint = self.get_account_endpoint(
            batch_account_name,
            resource_group).replace("https://", "")
        key = self.get_account_key(
            batch_account_name,
            resource_group)

        self.kwargs.update({
            'p_id': 'xplatCreatedPool',
            'acc_n': batch_account_name,
            'acc_k': key,
            'acc_u': endpoint
        })

        self.batch_cmd('batch pool create --id {p_id} --vm-size "standard_d2s_v3" '
                        '--image "canonical:0001-com-ubuntu-server-focal:20_04-lts" '
                        '--node-agent-sku-id "batch.node.ubuntu 20.04" '
                        '--target-dedicated-nodes 2 '
                        '--os-disk-size 100 '
                        '--os-disk-caching ReadWrite '
                        '--placement "CacheDisk" '
                        '--storage-account-type "StandardSSD_LRS" ')

        res = self.batch_cmd('batch pool show --pool-id {p_id}').get_output_in_json()
        print(res)

        self.assertTrue(res['virtualMachineConfiguration']['nodeAgentSkuId'])
        self.assertTrue(res['virtualMachineConfiguration']['osDisk']['caching'])
        self.assertTrue(res['virtualMachineConfiguration']['osDisk']['managedDisk']['storageAccountType'])
        self.assertTrue(res['virtualMachineConfiguration']['osDisk']['diskSizeGb'])
        self.assertTrue(res['virtualMachineConfiguration']['osDisk']['ephemeralOsDiskSettings']['placement'])

        self.batch_cmd('batch pool delete --pool-id {p_id} --yes')

    @ResourceGroupPreparer()
    @BatchAccountPreparer()
    def test_batch_pool_upgradePolicy_cmd(
            self,
            resource_group,
            batch_account_name):
        endpoint = self.get_account_endpoint(
            batch_account_name,
            resource_group).replace("https://", "")
        key = self.get_account_key(
            batch_account_name,
            resource_group)

        self.kwargs.update({
            'p_id': 'xplatCreatedPool',
            'acc_n': batch_account_name,
            'acc_k': key,
            'acc_u': endpoint
        })

        self.batch_cmd('batch pool create --id {p_id} --vm-size "standard_d4s_v3" '
                        '--image "MicrosoftWindowsServer:WindowsServer:2016-datacenter-smalldisk" '
                        '--node-agent-sku-id "batch.node.windows amd64" '
                        '--policy "zonal" '
                        '--target-dedicated-nodes 2 '
                        '--upgrade-policy-mode "automatic" '
                        '--disable-auto-rollback '
                        '--enable-auto-os-upgrade '
                        '--defer-os-rolling-upgrade '
                        '--use-rolling-upgrade-policy '
                        '--enable-cross-zone-upgrade '
                        '--max-batch-instance-percent 20 '
                        '--max-unhealthy-instance-percent 20 '
                        '--max-unhealthy-upgraded-instance-percent 20 '
                        '--pause-time-between-batches "PT0S" '
                        '--prioritize-unhealthy-instances '
                        '--rollback-failed-instances-on-policy-breach ')

        res = self.batch_cmd('batch pool show --pool-id {p_id}').get_output_in_json()
        print(res)

        self.assertTrue(res['upgradePolicy']['mode'])
        self.assertTrue(res['upgradePolicy']['automaticOsUpgradePolicy']['disableAutomaticRollback'])
        self.assertTrue(res['upgradePolicy']['automaticOsUpgradePolicy']['enableAutomaticOsUpgrade'])
        self.assertTrue(res['upgradePolicy']['automaticOsUpgradePolicy']['osRollingUpgradeDeferral'])
        self.assertTrue(res['upgradePolicy']['automaticOsUpgradePolicy']['useRollingUpgradePolicy'])
        self.assertTrue(res['upgradePolicy']['rollingUpgradePolicy']['enableCrossZoneUpgrade'])
        self.assertEqual(res['upgradePolicy']['rollingUpgradePolicy']['maxBatchInstancePercent'], 20)
        self.assertEqual(res['upgradePolicy']['rollingUpgradePolicy']['maxUnhealthyInstancePercent'], 20)
        self.assertEqual(res['upgradePolicy']['rollingUpgradePolicy']['maxUnhealthyUpgradedInstancePercent'], 20)
        self.assertTrue(res['upgradePolicy']['rollingUpgradePolicy']['pauseTimeBetweenBatches'], '')
        self.assertTrue(res['upgradePolicy']['rollingUpgradePolicy']['prioritizeUnhealthyInstances'])
        self.assertTrue(res['upgradePolicy']['rollingUpgradePolicy']['rollbackFailedInstancesOnPolicyBreach'])

        self.batch_cmd('batch pool delete --pool-id {p_id} --yes')

    @ResourceGroupPreparer()
    @BatchAccountPreparer()
    def test_batch_pool_enableAcceleratedNetworking_cmd(
            self,
            resource_group,
            batch_account_name):
        endpoint = self.get_account_endpoint(
            batch_account_name,
            resource_group).replace("https://", "")
        key = self.get_account_key(
            batch_account_name,
            resource_group)

        self.kwargs.update({
            'p_id': 'xplatCreatedPool',
            'acc_n': batch_account_name,
            'acc_k': key,
            'acc_u': endpoint
        })
        self.batch_cmd('batch pool create --id {p_id} --image "MicrosoftWindowsServer:WindowsServer:2016-datacenter-smalldisk"  --target-dedicated-nodes 2 --vm-size "standard_d2_v2" --node-agent-sku-id "batch.node.windows amd64" --accelerated-networking true')

        self.assertTrue(self.batch_cmd('batch pool show --pool-id {p_id}').get_output_in_json()['networkConfiguration']['enableAcceleratedNetworking'])

        self.batch_cmd('batch pool delete --pool-id {p_id} --yes')

    @ResourceGroupPreparer()
    @BatchAccountPreparer()
    def test_batch_job_list_cmd(
            self,
            resource_group,
            batch_account_name):
        self.set_account_info(batch_account_name, resource_group)
        self.kwargs.update({
            'j_id': 'xplatJob',
            'js_id': 'xplatJobScheduleJobTests',
            'j_file': self._get_test_data_file('batchCreateJob.json'),
            'js_file': self._get_test_data_file('batchCreateJobScheduleForJobTests.json')
        })

        self.batch_cmd('batch job-schedule create --json-file "{js_file}"')
        self.addCleanup(lambda: self.batch_cmd('batch job-schedule delete --job-schedule-id {js_id} --yes'))

        self.batch_cmd('batch job create --json-file "{j_file}"')
        self.batch_cmd('batch job list --job-schedule-id {js_id}').assert_with_checks([
            self.check('length(@)', 1),
            self.check('[0].id', 'xplatJobScheduleJobTests:job-1')])

        result = self.batch_cmd('batch job list') \
            .assert_with_checks([self.check('length(@)', 2)]) \
            .get_output_in_json()

        self.assertTrue(any([i for i in result if i['id'] == 'xplatJobScheduleJobTests:job-1']))
        self.assertTrue(any([i for i in result if i['id'] == 'xplatJob']))

        self.batch_cmd('batch job delete --job-id {j_id} --yes')

    @ResourceGroupPreparer()
    @BatchAccountPreparer(location='eastus2')
    def test_batch_task_create_cmd(self, resource_group, batch_account_name):
        self.set_account_info(batch_account_name, resource_group)
        self.kwargs.update({
            'j_id': 'xplatJobForTaskTests',
            't_id': 'xplatTask',
            'j_file': self._get_test_data_file('batchCreateJobForTaskTests.json'),
            't_file': self._get_test_data_file('batchCreateTask.json'),
            'ts_file': self._get_test_data_file('batchCreateMultiTasks.json')
        })

        self.batch_cmd('batch job create --json-file "{j_file}"')
        self.addCleanup(lambda: self.batch_cmd('batch job delete --job-id {j_id} --yes'))

        self.batch_cmd('batch task create --job-id {j_id} --json-file "{t_file}"').assert_with_checks([
            self.check('id', 'xplatTask'),
            self.check('commandLine', 'cmd /c dir /s')])

        self.batch_cmd('batch task show --job-id {j_id} --task-id {t_id}').assert_with_checks([
            self.check('userIdentity.autoUser.scope', 'pool')])

        self.batch_cmd('batch task delete --job-id {j_id} --task-id {t_id} --yes')

        self.batch_cmd('batch task create --job-id {j_id} --task-id aaa'
                       ' --command-line "ping 127.0.0.1 -n 30" --max-wall-clock-time P3Y6M4DT12H30M5S').assert_with_checks([
                           self.check('id', 'aaa'),
                           self.check('commandLine', 'ping 127.0.0.1 -n 30')])

        task_result = self.batch_cmd('batch job task-counts show --job-id {j_id}').get_output_in_json()
        if self.is_live or self.in_recording or task_result["taskCounts"]["active"] == 0:
            time.sleep(10)

        task_result = self.batch_cmd('batch job task-counts show --job-id {j_id}').get_output_in_json()

        self.assertEqual(task_result["taskCounts"]["completed"], 0)
        self.assertEqual(task_result["taskCounts"]["active"], 1)
        self.assertEqual(task_result["taskSlotCounts"]["completed"], 0)
        self.assertEqual(task_result["taskSlotCounts"]["active"], 1)

        self.batch_cmd('batch task delete --job-id {j_id} --task-id aaa --yes')

        result = self.batch_cmd('batch task create --job-id {j_id} --json-file "{ts_file}"')
        result = result.get_output_in_json()
        self.assertEqual(len(result), 3)
        self.assertTrue(any([i for i in result if i['taskId'] == 'xplatTask1']))

    @ResourceGroupPreparer()
    @BatchAccountPreparer(location='eastus2')
    def test_batch_file_download_cmd(self, resource_group, batch_account_name):
        self.set_account_info(batch_account_name, resource_group)
        self.kwargs.update({
            'j_id': 'xplatJobForTaskTests',
            't_id': 'xplatTask1',
            'p_id': 'xplatTestPool',
            'j_file': self._get_test_data_file('batchCreateJobForTaskTests.json'),
            'p_file': self._get_test_data_file('batchCreateTestPool.json'),
            'ts_file': self._get_test_data_file('batchCreateMultiTasks.json')
        })
        # create a pool, job and task
        self.batch_cmd('batch pool create --json-file "{p_file}"')
        self.batch_cmd('batch job create --json-file "{j_file}"')
        self.batch_cmd('batch task create --job-id {j_id} --json-file "{ts_file}"')

        self.wait_for_task_complete("xplatJobForTaskTests", 3)

        temp_dir = self.create_temp_dir()

        # verify task file download
        task_stdout = os.path.join(temp_dir, "task_stdout.txt")
        self.kwargs.update({'task_stdout': task_stdout})
        self.batch_cmd('batch task file download --destination "{task_stdout}" --file-path stdout.txt --job-id {j_id} --task-id {t_id}')
        self.assertTrue(os.path.isfile(task_stdout), f'File {task_stdout} does not exist.')
        self.assertGreater(os.path.getsize(task_stdout), 0, f'File {task_stdout} is empty.')

        task_stdout_range = os.path.join(temp_dir, "task_stdout_range.txt")
        self.kwargs.update({'task_stdout_range': task_stdout_range})
        self.batch_cmd('batch task file download --destination "{task_stdout_range}" --file-path stdout.txt --job-id {j_id} --task-id {t_id} --start-range 1 --end-range 2')
        self.assertTrue(os.path.isfile(task_stdout_range), f'File {task_stdout_range} does not exist.')
        self.assertEqual(os.path.getsize(task_stdout_range), 2)

        self.assertGreater(os.path.getsize(task_stdout), os.path.getsize(task_stdout_range), f'File {task_stdout_range} should be smaller due to range limits.')

        # verify node file download
        nodes = self.batch_cmd('batch node list --pool-id {p_id}').get_output_in_json()
        self.assertTrue(len(nodes) > 0)
        self.kwargs.update({'node1': nodes[0]['id']})

        node_stdout = os.path.join(temp_dir, "node_stdout.txt")
        self.kwargs.update({'node_stdout': node_stdout})
        self.batch_cmd('batch node file download --destination "{node_stdout}" --file-path startup/stdout.txt --node-id {node1} --pool-id {p_id}')
        self.assertTrue(os.path.isfile(node_stdout), f'File {node_stdout} does not exist.')
        self.assertGreater(os.path.getsize(node_stdout), 0, f'File {node_stdout} is empty.')

        node_stdout_range = os.path.join(temp_dir, "node_stdout_range.txt")
        self.kwargs.update({'node_stdout_range': node_stdout_range})
        self.batch_cmd('batch node file download --destination "{node_stdout_range}" --file-path startup/stdout.txt --node-id {node1} --pool-id {p_id} --start-range 1 --end-range 2')
        self.assertTrue(os.path.isfile(node_stdout_range), f'File {node_stdout_range} does not exist.')
        self.assertEqual(os.path.getsize(node_stdout_range), 2)

        self.assertGreater(os.path.getsize(node_stdout), os.path.getsize(node_stdout_range), f'File {node_stdout_range} should be smaller due to range limits.')

    @ResourceGroupPreparer()
    @BatchAccountPreparer(location='eastus2')
    def test_batch_jobs_and_tasks(self, resource_group, batch_account_name):
        self.set_account_info(batch_account_name, resource_group)
        self.kwargs.update({
            'p_id': 'xplatJobForTaskTests',
            'j_id': "cli-test-job-1",
            't_id': 'cli-test-task-1'
        })

        # test create pool using parameters
        self.batch_cmd('batch pool create --id {p_id} --vm-size Standard_DS1_v2 '
                                '--image canonical:ubuntuserver:18.04-lts --node-agent-sku-id "batch.node.ubuntu 18.04" '
                                '--disk-encryption-targets "TemporaryDisk"')

        # test create job with missing parameters
        self.kwargs['start'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        with self.assertRaises(SystemExit):
            self.batch_cmd('batch job create --id {j_id} --metadata test=value '
                           '--job-manager-task-environment-settings a=b '
                           '--job-max-task-retry-count 5 ')

        # test create job
        self.batch_cmd('batch job create --id {j_id} --metadata test=value '
                       '--job-max-task-retry-count 5 '
                       '--job-manager-task-id JobManager '
                       '--job-manager-task-command-line "cmd /c set AZ_BATCH_TASK_ID" '
                       '--job-manager-task-environment-settings '
                       'CLI_TEST_VAR=CLI_TEST_VAR_VALUE --pool-id {p_id}')

        # test get job
        self.batch_cmd('batch job show --job-id {j_id}').assert_with_checks([
            self.check('onAllTasksComplete', 'noaction'),
            self.check('constraints.maxTaskRetryCount', 5),
            self.check('jobManagerTask.id', 'JobManager'),
            self.check('jobManagerTask.environmentSettings[0].name', 'CLI_TEST_VAR'),
            self.check('jobManagerTask.environmentSettings[0].value', 'CLI_TEST_VAR_VALUE'),
            self.check('metadata[0].name', 'test'),
            self.check('metadata[0].value', 'value')])

        # test bad enum value
        with self.assertRaises(CLIError):
            self.batch_cmd('batch job set --job-id {j_id} --on-all-tasks-complete badValue ')

        # test patch job
        self.batch_cmd('batch job set --job-id {j_id} --job-max-wall-clock-time P3Y6M4DT12H30M5S '
                       '--on-all-tasks-complete terminatejob')
        self.batch_cmd('batch job show --job-id {j_id}').assert_with_checks([
            self.check('onAllTasksComplete', 'terminatejob'),
            self.check('constraints.maxTaskRetryCount', 0),
            self.check('constraints.maxWallClockTime', 'P1279DT12H30M5S'),
            self.check('jobManagerTask.id', 'JobManager'),
            self.check('jobManagerTask.environmentSettings[0].name', 'CLI_TEST_VAR'),
            self.check('jobManagerTask.environmentSettings[0].value', 'CLI_TEST_VAR_VALUE'),
            self.check('metadata[0].name', 'test'),
            self.check('metadata[0].value', 'value')])

        # test filter/header argument
        self.batch_cmd('batch job reset --job-id {j_id} --pool-id {p_id} --on-all-tasks-complete '
                       'terminatejob --if-unmodified-since {start}', expect_failure=True)

        # test reset job
        self.batch_cmd('batch job reset --job-id {j_id} --pool-id {p_id}  '
                       '--on-all-tasks-complete terminatejob ')
        job = self.batch_cmd('batch job show --job-id {j_id}').assert_with_checks([
            self.check('constraints.maxTaskRetryCount', 0),
            self.check('metadata', None)])

        job = job.get_output_in_json()
        self.assertFalse(job['constraints']['maxWallClockTime'] == '1279 days, 12:30:05')

        # task list (already have a job manager task)
        task_list = self.batch_cmd('batch task list --job-id {j_id}').get_output_in_json()
        self.assertEqual(len(task_list), 1)

        # task create
        self.batch_cmd('batch task create --job-id {j_id} --task-id {t_id} --command-line "sleep 60"').assert_with_checks([
            self.check('id', 'cli-test-task-1'),
            self.check('commandLine', 'sleep 60'),
            self.check('constraints.maxTaskRetryCount', 0)])

        # task show
        self.batch_cmd('batch task show --job-id {j_id} --task-id {t_id}').assert_with_checks([
            self.check('id', 'cli-test-task-1'),
            self.check('userIdentity.autoUser.scope', 'pool'),
            self.check('requiredSlots', 1),
            self.check('constraints.maxTaskRetryCount', 0)])

        # task list shows 2nd task
        task_list = self.batch_cmd('batch task list --job-id {j_id}').get_output_in_json()
        self.assertEqual(len(task_list), 2)

        # task reset
        self.batch_cmd('batch task reset --job-id {j_id} --task-id {t_id} --max-task-retry-count 3 --max-wall-clock-time PT0H20M --retention-time P3Y6M4DT12H30M5S')
        self.batch_cmd('batch task show --job-id {j_id} --task-id {t_id}').assert_with_checks([
            self.check('id', 'cli-test-task-1'),
            self.check('constraints.maxTaskRetryCount', 3)])

        # task stop
        self.batch_cmd('batch task stop --job-id {j_id} --task-id {t_id}')
        self.batch_cmd('batch task show --job-id {j_id} --task-id {t_id}').assert_with_checks([
            self.check('id', 'cli-test-task-1'),
            self.check('state', 'completed'),
            self.check('executionInfo.failureInfo.category', 'UserError')])

        # task reactivate
        self.batch_cmd('batch task reactivate --job-id {j_id} --task-id {t_id}')
        self.batch_cmd('batch task show --job-id {j_id} --task-id {t_id}').assert_with_checks([
            self.check('id', 'cli-test-task-1'),
            self.check('state', 'active')])

        # task delete
        self.batch_cmd('batch task delete --job-id {j_id} --task-id {t_id} --yes')

    @ResourceGroupPreparer()
    @BatchAccountPreparer()
    def test_batch_pools_and_nodes(
            self,
            resource_group,
            batch_account_name):  # pylint:disable=too-many-statements
        self.set_account_info(batch_account_name, resource_group)
        self.kwargs.update({
            'pool_i': "azure-cli-test-iaas",
            'pool_j': "azure-cli-test-json"
        })

        # test create pool using parameters
        self.batch_cmd('batch pool create --id {pool_i} --vm-size Standard_DS1_v2 '
                       '--image Canonical:UbuntuServer:18.04-LTS '
                       '--node-agent-sku-id "batch.node.ubuntu 18.04"')
        
        # test that deprecated --target-communication argument causes argparse error
        with self.assertRaises(SystemExit):
            self.batch_cmd('batch pool create --id test-deprecated-arg --vm-size Standard_DS1_v2 '
                           '--image Canonical:UbuntuServer:18.04-LTS '
                           '--node-agent-sku-id "batch.node.ubuntu 18.04" '
                           '--target-communication classic')
        
        # test that the deprecated targetNodeCommunicationMode property is not included in pool show output
        pool_result = self.batch_cmd('batch pool show --pool-id {pool_i}').get_output_in_json()
        self.assertNotIn('targetNodeCommunicationMode', pool_result, 'targetNodeCommunicationMode should not be present in pool output')

        # test create pool with missing parameters
        with self.assertRaises(SystemExit):
            self.batch_cmd('batch pool create --id missing-params-test --image Canonical:UbuntuServer:18.04-LTS')

        # test create pool with invalid vm size
        with self.assertRaisesRegex(CLIError, r"The value provided for one of the properties in the request body is invalid"):
            self.batch_cmd('batch pool create --id invalid-size-test --vm-size thisisinvalid '
                           '--image Canonical:UbuntuServer:16.04.0-LTS --node-agent-sku-id '
                           '"batch.node.ubuntu 16.04"')

        # test create pool with missing optional parameters
        with self.assertRaises(SystemExit):
            self.batch_cmd('batch pool create --id missing-optional-test --vm-size Standard_DS1_v2 '
                           '--start-task-wait-for-success')

        # test create pool from JSON file
        self.kwargs['json'] = self._get_test_data_file('batch-pool-create.json').replace('\\', '\\\\')
        self.batch_cmd('batch pool create --json-file "{json}"')
        self.batch_cmd('batch pool show --pool-id azure-cli-test-json').assert_with_checks([
            self.check('userAccounts[0].name', 'cliTestUser'),
            self.check('startTask.userIdentity.username', 'cliTestUser'),
            self.check('taskSlotsPerNode', 3)
        ])

        # test create pool from non-existant JSON file
        with self.assertRaises(SystemExit):
            self.batch_cmd('batch pool create --json-file batch-pool-create-missing.json')

        # test create pool from invalid JSON file
        with self.assertRaises(CLIError):
            self.kwargs['json'] = self._get_test_data_file('batch-pool-create-invalid.json').replace('\\', '\\\\')
            self.batch_cmd('batch pool create --json-file "{json}"')

        # test create pool from JSON file with additional parameters
        with self.assertRaises(SystemExit):
            self.kwargs['json'] = self._get_test_data_file('batch-pool-create.json').replace('\\', '\\\\')
            self.batch_cmd('batch pool create --json-file "{json}" --vm-size small')

        # test list pools
        pool_list = self.batch_cmd('batch pool list')
        pool_list = pool_list.get_output_in_json()
        self.assertEqual(len(pool_list), 2)
        pool_ids = sorted([p['id'] for p in pool_list])
        self.assertEqual(pool_ids, ["azure-cli-test-iaas", "azure-cli-test-json"])

        # test list pools with select
        pool_list = self.batch_cmd('batch pool list --filter "id eq \'{pool_i}\'"').get_output_in_json()
        self.assertEqual(len(pool_list), 1)

        self.wait_for_pool_steady("azure-cli-test-iaas")

        # test resize pool
        self.batch_cmd('batch pool resize --pool-id {pool_i} --target-dedicated-nodes 0 --target-low-priority-nodes 5')
        self.batch_cmd('batch pool show --pool-id {pool_i} '
                       '--select "allocationState, targetLowPriorityNodes"').assert_with_checks([
                           self.check('targetLowPriorityNodes', 5)])

        # test cancel pool resize
        self.batch_cmd('batch pool resize --pool-id {pool_i} --abort')

        # test enable autoscale
        self.batch_cmd('batch pool autoscale enable --pool-id {pool_i} '
                       '--auto-scale-formula "$TargetLowPriorityNodes=3"')
        self.batch_cmd('batch pool show --pool-id {pool_i} --select "enableAutoScale"').assert_with_checks([
            self.check('enableAutoScale', True)])

        # test evaluate autoscale
        self.batch_cmd('batch pool autoscale evaluate --pool-id {pool_i} '
                       '--auto-scale-formula "$TargetLowPriorityNodes=3"')

        # test disable autoscale
        self.batch_cmd('batch pool autoscale disable --pool-id {pool_i}')
        self.batch_cmd('batch pool show --pool-id {pool_i} --select "enableAutoScale"').assert_with_checks([
            self.check('enableAutoScale', False)])

        # Pool list usage metrics command exists but the API is retired
        # TODO: Remove this test when the usage metrics CLI command is removed
        with self.assertRaisesRegex(CLIError, r".*Pool list usage metrics API was retired.*"):
            self.batch_cmd('batch pool usage-metrics list')

        # TODO: Test update pool from JSON file

        # test patch pool using parameters
        current = self.batch_cmd('batch pool show --pool-id {pool_j} --select "startTask"').get_output_in_json()
        self.batch_cmd('batch pool set --pool-id {pool_j} --start-task-command-line new_value')
        updated = self.batch_cmd('batch pool show --pool-id {pool_j} --select "startTask"').get_output_in_json()
        self.assertNotEqual(current['startTask']['commandLine'], updated['startTask']['commandLine'])

        # test list node agent skus
        self.batch_cmd('batch pool supported-images list')

        # test deprecated --target-communication for pool set
        with self.assertRaises(SystemExit):
            self.batch_cmd('batch pool set --pool-id {pool_i} --target-communication classic')

        # test app package reference
        self.batch_cmd('batch pool set --pool-id {pool_i} --application-package-references does-not-exist',
                       expect_failure=True)

        self.wait_for_pool_steady("azure-cli-test-iaas")

        # scale up to test node commands
        self.batch_cmd('batch pool resize --pool-id {pool_i} --target-dedicated-nodes 1')
        self.wait_for_pool_steady("azure-cli-test-iaas")

        # node list
        node_list = self.batch_cmd("batch node list --pool-id {pool_i}").get_output_in_json()
        self.assertEqual(len(node_list), 1)
        self.kwargs.update({'node1': node_list[0]['id']})

        # test that deprecated currentNodeCommunicationMode property is not present in pool output
        self.assertNotIn('currentNodeCommunicationMode', node_list, 'currentNodeCommunicationMode should not be present in pool output')

        # node show
        self.batch_cmd('batch node show --pool-id {pool_i} --node-id {node1}').assert_with_checks([
            self.check('id', self.kwargs['node1']),
            self.check('isDedicated', True)])

        # node reboot
        self.batch_cmd('batch node reboot --pool-id {pool_i} --node-id {node1}')
        self.batch_cmd('batch node show --pool-id {pool_i} --node-id {node1}').assert_with_checks([
            self.check('id', self.kwargs['node1']),
            self.check('state', 'rebooting')])

        # node delete
        self.batch_cmd('batch node delete --pool-id {pool_i} --node-list {node1}')

        # pool delete
        self.batch_cmd('batch pool delete --pool-id {pool_i} --yes')

    def wait_for_pool_steady(self, pool_id, timeout_seconds=120):
        start_time = time.time()
        while True:
            pool = self.batch_cmd(f"batch pool show --pool-id {pool_id}").get_output_in_json()
            if pool["allocationState"] == "steady":
                return
            elapsed_seconds = time.time() - start_time
            if elapsed_seconds > timeout_seconds:
                raise TimeoutError("Timed out waiting for pool to reach steady state")
            if self.is_live or self.in_recording:
                time.sleep(2)

    def wait_for_task_complete(self, job_id, tasks=0, timeout_seconds=300):
        start_time = time.time()

        while True:
            task_result = self.batch_cmd(f"batch job task-counts show --job-id {job_id}").get_output_in_json()
            if task_result["taskCounts"]["completed"] == tasks:
                return
            elapsed_seconds = time.time() - start_time
            if elapsed_seconds > timeout_seconds:
                raise TimeoutError("Timed out waiting for pool to reach steady state")

            if self.is_live or self.in_recording:
                time.sleep(30)
