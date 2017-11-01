# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import datetime

from knack.util import CLIError
from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, JMESPathCheck
from .batch_preparers import BatchAccountPreparer, BatchScenarioMixin


class BatchDataPlaneScenarioTests(BatchScenarioMixin, ScenarioTest):

    def _get_test_data_file(self, filename):
        filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', filename)
        self.assertTrue(os.path.isfile(filepath), 'File {} does not exist.'.format(filepath))
        return filepath

    @ResourceGroupPreparer()
    @BatchAccountPreparer(location='northcentralus')
    def test_batch_certificate_cmd(self, resource_group, batch_account_name):
        create_cert_file_path = self._get_test_data_file('batchtest.cer')
        cert_thumbprint = '59833fd835f827e9ec693a4c82435a6360cc6271'

        # test create certificate with default set
        account_info = self.get_account_info(batch_account_name, resource_group)

        self.batch_cmd('batch certificate create --thumbprint {} --certificate-file "{}"',
                       account_info, cert_thumbprint, create_cert_file_path) \
            .assert_with_checks([JMESPathCheck('thumbprint', cert_thumbprint),
                                 JMESPathCheck('thumbprintAlgorithm', 'sha1'),
                                 JMESPathCheck('state', 'active')])

        # test create account with default set
        self.batch_cmd('batch certificate list', account_info).assert_with_checks(
            [JMESPathCheck('length(@)', 1), JMESPathCheck('[0].thumbprint', cert_thumbprint)])

        self.batch_cmd("batch certificate delete --thumbprint {} --yes", account_info,
                       cert_thumbprint)

        self.batch_cmd('batch certificate show --thumbprint {}', account_info, cert_thumbprint) \
            .assert_with_checks([JMESPathCheck('thumbprint', cert_thumbprint),
                                 JMESPathCheck('thumbprintAlgorithm', 'sha1'),
                                 JMESPathCheck('state', 'deleting')])

    @ResourceGroupPreparer()
    @BatchAccountPreparer(location='japanwest')
    def test_batch_pool_cmd(self, resource_group, batch_account_name):
        account_info = self.get_account_info(batch_account_name, resource_group)
        create_pool_file_path = self._get_test_data_file('batchCreatePool.json')
        update_pool_file_path = self._get_test_data_file('batchUpdatePool.json')
        create_pool_id = 'xplatCreatedPool'
        is_playback = os.path.exists(self.recording_file)

        self.batch_cmd('batch pool create --json-file "{}"', account_info, create_pool_file_path)

        result = self.batch_cmd('batch pool create --id pool_image1 --vm-size Standard_A1 '
                                '--image a:b:c --node-agent-sku-id "batch.node.windows amd64"',
                                account_info, create_pool_file_path, expect_failure=True)

        result = self.batch_cmd('batch pool create --id pool_image1 --vm-size Standard_A1 '
                                '--image /subscriptions/11111111-1111-1111-1111-111111111111'
                                '/resourceGroups/test_rg/providers/Microsoft.Compute/images/custom_image '
                                '--node-agent-sku-id "batch.node.windows amd64"',
                                account_info, create_pool_file_path, expect_failure=True)

        result = self.batch_cmd('batch pool show --pool-id {}', account_info, create_pool_id) \
            .assert_with_checks([JMESPathCheck('allocationState', 'steady'),
                                 JMESPathCheck('id', create_pool_id),
                                 JMESPathCheck('startTask.commandLine', "cmd /c echo test"),
                                 JMESPathCheck('startTask.userIdentity.autoUser.elevationLevel',
                                               "admin")])
        target = result.get_output_in_json()['currentDedicatedNodes']
        self.batch_cmd('batch pool resize --pool-id {} --target-dedicated-nodes 5 '
                       '--target-low-priority-nodes 3', account_info, create_pool_id)
        self.batch_cmd('batch pool show --pool-id {}', account_info, create_pool_id) \
            .assert_with_checks([JMESPathCheck('allocationState', 'resizing'),
                                 JMESPathCheck('targetDedicatedNodes', 5),
                                 JMESPathCheck('targetLowPriorityNodes', 3),
                                 JMESPathCheck('id', create_pool_id)])

        self.batch_cmd('batch pool resize --pool-id {} --abort', account_info, create_pool_id)
        if not is_playback:
            import time
            time.sleep(120)

        self.batch_cmd('batch pool show --pool-id {}', account_info, create_pool_id) \
            .assert_with_checks([JMESPathCheck('allocationState', 'steady'),
                                 JMESPathCheck('id', create_pool_id),
                                 JMESPathCheck('currentDedicatedNodes', target),
                                 JMESPathCheck('targetDedicatedNodes', 5),
                                 JMESPathCheck('targetLowPriorityNodes', 3)])

        self.batch_cmd('batch pool reset --pool-id {} --json-file "{}"', account_info,
                       create_pool_id, update_pool_file_path) \
            .assert_with_checks([JMESPathCheck('allocationState', 'steady'),
                                 JMESPathCheck('id', create_pool_id),
                                 JMESPathCheck('startTask.commandLine', "cmd /c echo updated")])

        self.batch_cmd('batch pool reset --pool-id {} --start-task-command-line hostname '
                       '--metadata a=b c=d', account_info, create_pool_id) \
            .assert_with_checks([JMESPathCheck('allocationState', 'steady'),
                                 JMESPathCheck('id', create_pool_id),
                                 JMESPathCheck('startTask.commandLine', "hostname"),
                                 JMESPathCheck('length(metadata)', 2),
                                 JMESPathCheck('metadata[0].name', 'a'),
                                 JMESPathCheck('metadata[1].value', 'd')])

        self.batch_cmd('batch pool delete --pool-id {} --yes', account_info, create_pool_id)

    @ResourceGroupPreparer()
    @BatchAccountPreparer(location='eastus2')
    def test_batch_job_list_cmd(self, resource_group, batch_account_name):
        account_info = self.get_account_info(batch_account_name, resource_group)

        create_job_id = 'xplatJob'
        job_schedule_id = 'xplatJobScheduleJobTests'
        create_job_file_path = self._get_test_data_file('batchCreateJob.json')
        create_jobschedule_file_path = self._get_test_data_file(
            'batchCreateJobScheduleForJobTests.json')

        self.batch_cmd('batch job-schedule create --json-file "{}"', account_info,
                       create_jobschedule_file_path)

        self.addCleanup(
            lambda: self.batch_cmd('batch job-schedule delete --job-schedule-id {} --yes',
                                   account_info, job_schedule_id))

        self.batch_cmd('batch job create --json-file "{}"', account_info, create_job_file_path)
        self.batch_cmd('batch job list --job-schedule-id {}', account_info, job_schedule_id) \
            .assert_with_checks([JMESPathCheck('length(@)', 1),
                                 JMESPathCheck('[0].id', '{}:job-1'.format(job_schedule_id))])

        result = self.batch_cmd('batch job list', account_info) \
            .assert_with_checks([JMESPathCheck('length(@)', 2)]) \
            .get_output_in_json()

        self.assertTrue(any([i for i in result if i['id'] == '{}:job-1'.format(job_schedule_id)]))
        self.assertTrue(any([i for i in result if i['id'] == create_job_id]))

        self.batch_cmd('batch job delete --job-id {} --yes', account_info, create_job_id)

    @ResourceGroupPreparer()
    @BatchAccountPreparer(location='canadacentral')
    def test_batch_task_create_cmd(self, resource_group, batch_account_name):
        job_id = 'xplatJobForTaskTests'
        task_id = 'xplatTask'
        create_job_file_path = self._get_test_data_file('batchCreateJobForTaskTests.json')
        create_task_file_path = self._get_test_data_file('batchCreateTask.json')
        create_tasks_file_path = self._get_test_data_file('batchCreateMultiTasks.json')
        account_info = self.get_account_info(batch_account_name, resource_group)

        self.batch_cmd('batch job create --json-file "{}"', account_info, create_job_file_path)
        self.addCleanup(lambda:
                        self.batch_cmd('batch job delete --job-id {} --yes', account_info, job_id))

        self.batch_cmd('batch task create --job-id {} --json-file "{}"', account_info, job_id,
                       create_task_file_path) \
            .assert_with_checks([JMESPathCheck('id', task_id),
                                 JMESPathCheck('commandLine', 'cmd /c dir /s')])

        self.batch_cmd('batch task show --job-id {} --task-id {}', account_info, job_id, task_id) \
            .assert_with_checks([JMESPathCheck('userIdentity.autoUser.scope', 'pool'),
                                 JMESPathCheck('authenticationTokenSettings.access[0]', 'job')])

        self.batch_cmd('batch task delete --job-id {} --task-id {} --yes', account_info, job_id,
                       task_id)

        self.batch_cmd('batch task create --job-id {} --task-id aaa --command-line "echo hello"',
                       account_info, job_id) \
            .assert_with_checks(
                [JMESPathCheck('id', 'aaa'), JMESPathCheck('commandLine', 'echo hello')])

        task_counts = self.batch_cmd('batch job task-counts show --job-id {}',
                                     account_info, job_id).get_output_in_json()
        self.assertEqual(task_counts["completed"], 0)
        self.assertEqual(task_counts["active"], 1)

        self.batch_cmd('batch task delete --job-id {} --task-id aaa --yes', account_info, job_id)

        result = self.batch_cmd('batch task create --job-id {} --json-file "{}"', account_info,
                                job_id, create_tasks_file_path).get_output_in_json()
        self.assertEqual(len(result), 3)
        self.assertTrue(any([i for i in result if i['taskId'] == 'xplatTask1']))

    @ResourceGroupPreparer()
    @BatchAccountPreparer(location='canadaeast')
    def test_batch_jobs_and_tasks(self, resource_group, batch_account_name):
        pool_paas = "azure-cli-test-paas"
        job_id = "cli-test-job-1"
        account_info = self.get_account_info(batch_account_name, resource_group)

        # test create paas pool using parameters
        self.batch_cmd('batch pool create --id {} --vm-size small --os-family 4', account_info,
                       pool_paas)

        # test create job with missing parameters
        start_time = datetime.datetime.now().isoformat()
        with self.assertRaises(SystemExit):
            self.batch_cmd('batch job create --id {} --metadata test=value '
                           '--job-manager-task-environment-settings a=b '
                           '--job-max-task-retry-count 5 ', account_info, job_id)

        # test create job
        self.batch_cmd('batch job create --id {} --metadata test=value '
                       '--job-max-task-retry-count 5 '
                       '--job-manager-task-id JobManager '
                       '--job-manager-task-command-line "cmd /c set AZ_BATCH_TASK_ID" '
                       '--job-manager-task-environment-settings '
                       'CLI_TEST_VAR=CLI_TEST_VAR_VALUE --pool-id {}',
                       account_info, job_id, pool_paas)

        # test get job
        self.batch_cmd('batch job show --job-id {}', account_info, job_id) \
            .assert_with_checks([JMESPathCheck('onAllTasksComplete', 'noAction'),
                                 JMESPathCheck('constraints.maxTaskRetryCount', 5),
                                 JMESPathCheck('jobManagerTask.id', 'JobManager'),
                                 JMESPathCheck('jobManagerTask.environmentSettings[0].name', 'CLI_TEST_VAR'),
                                 JMESPathCheck('jobManagerTask.environmentSettings[0].value', 'CLI_TEST_VAR_VALUE'),
                                 JMESPathCheck('metadata[0].name', 'test'),
                                 JMESPathCheck('metadata[0].value', 'value')])

        # test bad enum value
        with self.assertRaises(SystemExit):
            self.batch_cmd('batch job set --job-id {} '
                           '--on-all-tasks-complete badValue ', account_info, job_id)

        # test patch job
        self.batch_cmd('batch job set --job-id {} --job-max-wall-clock-time P3Y6M4DT12H30M5S '
                       '--on-all-tasks-complete terminateJob', account_info, job_id)
        self.batch_cmd('batch job show --job-id {}', account_info, job_id) \
            .assert_with_checks([JMESPathCheck('onAllTasksComplete', 'terminateJob'),
                                 JMESPathCheck('constraints.maxTaskRetryCount', 0),
                                 JMESPathCheck('constraints.maxWallClockTime', '1279 days, 12:30:05'),
                                 JMESPathCheck('jobManagerTask.id', 'JobManager'),
                                 JMESPathCheck('jobManagerTask.environmentSettings[0].name', 'CLI_TEST_VAR'),
                                 JMESPathCheck('jobManagerTask.environmentSettings[0].value', 'CLI_TEST_VAR_VALUE'),
                                 JMESPathCheck('metadata[0].name', 'test'),
                                 JMESPathCheck('metadata[0].value', 'value')])

        # test filter/header argument
        with self.assertRaises(CLIError):
            self.batch_cmd('batch job reset --job-id {} --pool-id {} '
                           '--on-all-tasks-complete terminateJob '
                           '--if-unmodified-since {}', account_info, job_id, pool_paas, start_time)

        # test reset job
        self.batch_cmd('batch job reset --job-id {} --pool-id {}  '
                       '--on-all-tasks-complete terminateJob ', account_info, job_id, pool_paas)
        job = self.batch_cmd('batch job show --job-id {}', account_info, job_id) \
            .assert_with_checks([JMESPathCheck('constraints.maxTaskRetryCount', 0),
                                 JMESPathCheck('metadata', None)])
        job = job.get_output_in_json()
        self.assertFalse(job['constraints']['maxWallClockTime'] == '1279 days, 12:30:05')

        # TODO: test task commands

    @ResourceGroupPreparer()
    @BatchAccountPreparer(location='westeurope')
    def test_batch_pools_and_nodes(self, resource_group, batch_account_name):  # pylint:disable=too-many-statements
        pool_paas = "azure-cli-test-paas"
        pool_iaas = "azure-cli-test-iaas"
        pool_json = "azure-cli-test-json"
        account_info = self.get_account_info(batch_account_name, resource_group)

        # test create paas pool using parameters
        self.batch_cmd('batch pool create --id {} --vm-size small --os-family 4',
                       account_info, pool_paas)

        # test create iaas pool using parameters
        self.batch_cmd('batch pool create --id {} --vm-size Standard_A1 '
                       '--image Canonical:UbuntuServer:16.04.0-LTS '
                       '--node-agent-sku-id "batch.node.ubuntu 16.04"', account_info, pool_iaas)

        # test create pool with missing parameters
        with self.assertRaises(SystemExit):
            self.batch_cmd('batch pool create --id missing-params-test --os-family 4',
                           account_info)

        # test create pool with missing required mutually exclusive parameters
        with self.assertRaises(SystemExit):
            self.batch_cmd('batch pool create --id missing-required-group-test --vm-size small',
                           account_info)

        # test create pool with parameters from mutually exclusive groups
        with self.assertRaises(SystemExit):
            self.batch_cmd('batch pool create --id mutually-exclusive-test --vm-size small '
                           '--os-family 4 --image Canonical:UbuntuServer:16-LTS:latest',
                           account_info)

        # test create pool with invalid vm size for IaaS
        with self.assertRaises(SystemExit):
            self.batch_cmd('batch pool create --id invalid-size-test --vm-size small '
                           '--image Canonical:UbuntuServer:16.04.0-LTS --node-agent-sku-id '
                           '"batch.node.ubuntu 16.04"', account_info)

        # test create pool with missing optional parameters
        with self.assertRaises(SystemExit):
            self.batch_cmd('batch pool create --id missing-optional-test --vm-size small '
                           '--os-family 4 --start-task-wait-for-success', account_info)

        # test create pool from JSON file
        input_json = self._get_test_data_file('batch-pool-create.json').replace('\\', '\\\\')
        self.batch_cmd('batch pool create --json-file {}', account_info, input_json)
        self.batch_cmd('batch pool show --pool-id azure-cli-test-json', account_info) \
            .assert_with_checks([JMESPathCheck('userAccounts[0].name', 'cliTestUser'),
                                 JMESPathCheck('startTask.userIdentity.userName', 'cliTestUser')])

        # test create pool from non-existant JSON file
        with self.assertRaises(SystemExit):
            self.batch_cmd('batch pool create --json-file batch-pool-create-missing.json',
                           account_info)

        # test create pool from invalid JSON file
        with self.assertRaises(SystemExit):
            input_json = self._get_test_data_file('batch-pool-create-invalid.json').replace('\\', '\\\\')
            self.batch_cmd('batch pool create --json-file {}', account_info, input_json)

        # test create pool from JSON file with additional parameters
        with self.assertRaises(SystemExit):
            input_json = self._get_test_data_file('batch-pool-create.json').replace('\\', '\\\\')
            self.batch_cmd('batch pool create --json-file {} --vm-size small', account_info, input_json)

        # test list pools
        pool_list = self.batch_cmd('batch pool list', account_info)
        pool_list = pool_list.get_output_in_json()
        self.assertEqual(len(pool_list), 3)
        pool_ids = sorted([p['id'] for p in pool_list])
        self.assertEqual(pool_ids, [pool_iaas, pool_json, pool_paas])

        # test list pools with select
        pool_list = self.batch_cmd('batch pool list --filter "id eq \'{}\'"',
                                   account_info, pool_paas).get_output_in_json()
        self.assertEqual(len(pool_list), 1)

        # test resize pool
        self.batch_cmd('batch pool resize --pool-id {} --target-dedicated-nodes 5', account_info, pool_paas)
        self.batch_cmd('batch pool show --pool-id {} --select "allocationState, targetDedicatedNodes"',
                       account_info, pool_paas).assert_with_checks([
                           JMESPathCheck('allocationState', 'resizing'),
                           JMESPathCheck('targetDedicatedNodes', 5)])

        # test cancel pool resize
        self.batch_cmd('batch pool resize --pool-id {} --abort', account_info, pool_paas)

        # test enable autoscale
        self.batch_cmd('batch pool autoscale enable --pool-id {} --auto-scale-formula '
                       '"$TargetDedicatedNodes=3"', account_info, pool_iaas)
        self.batch_cmd('batch pool show --pool-id {} --select "enableAutoScale"',
                       account_info, pool_iaas).assert_with_checks([
                           JMESPathCheck('enableAutoScale', True)])

        # test evaluate autoscale
        self.batch_cmd('batch pool autoscale evaluate --pool-id {} --auto-scale-formula '
                       '"$TargetDedicatedNodes=3"', account_info, pool_iaas)

        # test disable autoscale
        self.batch_cmd('batch pool autoscale disable --pool-id {}', account_info, pool_iaas)
        self.batch_cmd('batch pool show --pool-id {} --select "enableAutoScale"',
                       account_info, pool_iaas).assert_with_checks([
                           JMESPathCheck('enableAutoScale', False)])

        # test list usage metrics
        self.batch_cmd('batch pool usage-metrics list', account_info)

        # TODO: Test update pool from JSON file

        # test patch pool using parameters
        current = self.batch_cmd('batch pool show --pool-id {} --select "startTask"',
                                 account_info, pool_json).get_output_in_json()
        self.batch_cmd('batch pool set --pool-id {} --start-task-command-line new_value',
                       account_info, pool_json)
        updated = self.batch_cmd('batch pool show --pool-id {} --select "startTask"',
                                 account_info, pool_json).get_output_in_json()
        self.assertNotEqual(current['startTask']['commandLine'],
                            updated['startTask']['commandLine'])

        # test list node agent skus
        self.batch_cmd('batch pool node-agent-skus list', account_info)

        # test delete iaas pool
        self.batch_cmd('batch pool delete --pool-id {} --yes', account_info, pool_iaas)
        self.batch_cmd('batch pool show --pool-id {} --select "state"',
                       account_info, pool_iaas).assert_with_checks([
                           JMESPathCheck('state', 'deleting')])

        # test app package reference
        with self.assertRaises(CLIError):
            self.batch_cmd('batch pool create --id app_package_test --vm-size small --os-family 4 '
                           '--application-package-references does-not-exist', account_info)
        with self.assertRaises(CLIError):
            self.batch_cmd('batch pool set --pool-id {} --application-package-references '
                           'does-not-exist', account_info, pool_paas)

        # TODO: Test node commands
