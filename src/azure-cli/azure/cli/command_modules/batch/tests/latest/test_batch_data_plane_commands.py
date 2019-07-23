# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import datetime

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer
from knack.util import CLIError
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
        self.kwargs.update({
            'cert': '59833fd835f827e9ec693a4c82435a6360cc6271',
            'cert_f': create_cert_file_path
        })

        # test create certificate with default set
        self.set_account_info(batch_account_name, resource_group)

        self.batch_cmd('batch certificate create --thumbprint {cert} '
                       '--certificate-file "{cert_f}"').assert_with_checks([
                           self.check('thumbprint', '{cert}'),
                           self.check('thumbprintAlgorithm', 'sha1'),
                           self.check('state', 'active')])

        # test create account with default set
        self.batch_cmd('batch certificate list').assert_with_checks([
            self.check('length(@)', 1),
            self.check('[0].thumbprint', '{cert}')])

        self.batch_cmd("batch certificate delete --thumbprint {cert} --yes")

        self.batch_cmd('batch certificate show --thumbprint {cert}').assert_with_checks([
            self.check('thumbprint', '{cert}'),
            self.check('thumbprintAlgorithm', 'sha1'),
            self.check('state', 'deleting')])

    @ResourceGroupPreparer()
    @BatchAccountPreparer(location='japanwest')
    def test_batch_pool_cmd(self, resource_group, batch_account_name):
        #
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
        result = self.batch_cmd('batch pool create --id pool_image1 --vm-size Standard_A1 '
                                '--image a:b:c --node-agent-sku-id "batch.node.windows amd64"',
                                expect_failure=True)

        result = self.batch_cmd('batch pool create --id pool_image1 --vm-size Standard_A1 '
                                '--image /subscriptions/11111111-1111-1111-1111-111111111111'
                                '/resourceGroups/test_rg/providers/Microsoft.Compute/images/custom_image '
                                '--node-agent-sku-id "batch.node.windows amd64"',
                                expect_failure=True)

        result = self.batch_cmd('batch pool show --pool-id {p_id}').assert_with_checks([
            self.check('allocationState', 'steady'),
            self.check('id', 'xplatCreatedPool'),
            self.check('startTask.commandLine', "cmd /c echo test"),
            self.check('startTask.userIdentity.autoUser.elevationLevel', "admin")])

        target = result.get_output_in_json()['currentDedicatedNodes']
        self.batch_cmd('batch pool resize --pool-id {p_id} --target-dedicated-nodes 5 '
                       '--target-low-priority-nodes 3')
        self.batch_cmd('batch pool show --pool-id {p_id}').assert_with_checks([
            self.check('allocationState', 'resizing'),
            self.check('targetDedicatedNodes', 5),
            self.check('targetLowPriorityNodes', 3),
            self.check('id', 'xplatCreatedPool')])

        self.batch_cmd('batch pool node-counts list').assert_with_checks([
            self.check('length(@)', 1),
            self.check('[0].poolId', 'xplatCreatedPool'),
            self.check('[0].dedicated.total', 0),
            self.check('[0].lowPriority.total', 0)])

        self.batch_cmd('batch pool resize --pool-id {p_id} --abort')
        if self.is_live or self.in_recording:
            import time
            time.sleep(120)

        self.batch_cmd('batch pool show --pool-id {p_id}').assert_with_checks([
            self.check('allocationState', 'steady'),
            self.check('id', 'xplatCreatedPool'),
            self.check('currentDedicatedNodes', target),
            self.check('targetDedicatedNodes', 5),
            self.check('targetLowPriorityNodes', 3)])

        self.batch_cmd('batch pool reset --pool-id {p_id} --json-file "{u_file}"').assert_with_checks([
            self.check('allocationState', 'steady'),
            self.check('id', 'xplatCreatedPool'),
            self.check('startTask.commandLine', "cmd /c echo updated")])

        self.batch_cmd('batch pool reset --pool-id {p_id} --start-task-command-line hostname '
                       '--metadata a=b c=d').assert_with_checks([
                           self.check('allocationState', 'steady'),
                           self.check('id', 'xplatCreatedPool'),
                           self.check('startTask.commandLine', "hostname"),
                           self.check('length(metadata)', 2),
                           self.check('metadata[0].name', 'a'),
                           self.check('metadata[1].value', 'd')])

        self.batch_cmd('batch pool delete --pool-id {p_id} --yes')

    @ResourceGroupPreparer()
    @BatchAccountPreparer(location='eastus')
    def test_batch_job_list_cmd(self, resource_group, batch_account_name):
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
    @BatchAccountPreparer(location='canadacentral')
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
            self.check('userIdentity.autoUser.scope', 'pool'),
            self.check('authenticationTokenSettings.access[0]', 'job')])

        self.batch_cmd('batch task delete --job-id {j_id} --task-id {t_id} --yes')

        self.batch_cmd('batch task create --job-id {j_id} --task-id aaa'
                       ' --command-line "ping 127.0.0.1 -n 30"').assert_with_checks([
                           self.check('id', 'aaa'),
                           self.check('commandLine', 'ping 127.0.0.1 -n 30')])

        if self.is_live or self.in_recording:
            import time
            time.sleep(10)
        task_counts = self.batch_cmd('batch job task-counts show --job-id {j_id}').get_output_in_json()
        self.assertEqual(task_counts["completed"], 0)
        self.assertEqual(task_counts["active"], 1)

        self.batch_cmd('batch task delete --job-id {j_id} --task-id aaa --yes')

        result = self.batch_cmd('batch task create --job-id {j_id} --json-file "{ts_file}"')
        result = result.get_output_in_json()
        self.assertEqual(len(result), 3)
        self.assertTrue(any([i for i in result if i['taskId'] == 'xplatTask1']))

    @ResourceGroupPreparer()
    @BatchAccountPreparer(location='canadaeast')
    def test_batch_jobs_and_tasks(self, resource_group, batch_account_name):
        self.set_account_info(batch_account_name, resource_group)
        self.kwargs.update({
            'p_id': 'xplatJobForTaskTests',
            'j_id': "cli-test-job-1",
        })

        # test create paas pool using parameters
        self.batch_cmd('batch pool create --id {p_id} --vm-size small --os-family 4')

        # test create job with missing parameters
        self.kwargs['start'] = datetime.datetime.now().isoformat()
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
        with self.assertRaises(SystemExit):
            self.batch_cmd('batch job set --job-id {j_id} --on-all-tasks-complete badValue ')

        # test patch job
        self.batch_cmd('batch job set --job-id {j_id} --job-max-wall-clock-time P3Y6M4DT12H30M5S '
                       '--on-all-tasks-complete terminatejob')
        self.batch_cmd('batch job show --job-id {j_id}').assert_with_checks([
            self.check('onAllTasksComplete', 'terminatejob'),
            self.check('constraints.maxTaskRetryCount', 0),
            self.check('constraints.maxWallClockTime', '1279 days, 12:30:05'),
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

        # TODO: test task commands

    @ResourceGroupPreparer()
    @BatchAccountPreparer(location='koreacentral')
    def test_batch_pools_and_nodes(self, resource_group, batch_account_name):  # pylint:disable=too-many-statements
        self.set_account_info(batch_account_name, resource_group)
        self.kwargs.update({
            'pool_p': "azure-cli-test-paas",
            'pool_i': "azure-cli-test-iaas",
            'pool_j': "azure-cli-test-json"
        })

        # test create paas pool using parameters
        self.batch_cmd('batch pool create --id {pool_p} --vm-size small --os-family 4')

        # test create iaas pool using parameters
        self.batch_cmd('batch pool create --id {pool_i} --vm-size Standard_A1 '
                       '--image Canonical:UbuntuServer:16.04.0-LTS '
                       '--node-agent-sku-id "batch.node.ubuntu 16.04"')

        # test create pool with missing parameters
        with self.assertRaises(SystemExit):
            self.batch_cmd('batch pool create --id missing-params-test --os-family 4')

        # test create pool with missing required mutually exclusive parameters
        with self.assertRaises(SystemExit):
            self.batch_cmd('batch pool create --id missing-required-group-test --vm-size small')

        # test create pool with parameters from mutually exclusive groups
        with self.assertRaises(SystemExit):
            self.batch_cmd('batch pool create --id mutually-exclusive-test --vm-size small '
                           '--os-family 4 --image Canonical:UbuntuServer:16-LTS:latest')

        # test create pool with invalid vm size for IaaS
        with self.assertRaises(SystemExit):
            self.batch_cmd('batch pool create --id invalid-size-test --vm-size small '
                           '--image Canonical:UbuntuServer:16.04.0-LTS --node-agent-sku-id '
                           '"batch.node.ubuntu 16.04"')

        # test create pool with missing optional parameters
        with self.assertRaises(SystemExit):
            self.batch_cmd('batch pool create --id missing-optional-test --vm-size small '
                           '--os-family 4 --start-task-wait-for-success')

        # test create pool from JSON file
        self.kwargs['json'] = self._get_test_data_file('batch-pool-create.json').replace('\\', '\\\\')
        self.batch_cmd('batch pool create --json-file {json}')
        self.batch_cmd('batch pool show --pool-id azure-cli-test-json').assert_with_checks([
            self.check('userAccounts[0].name', 'cliTestUser'),
            self.check('startTask.userIdentity.userName', 'cliTestUser')])

        # test create pool from non-existant JSON file
        with self.assertRaises(SystemExit):
            self.batch_cmd('batch pool create --json-file batch-pool-create-missing.json')

        # test create pool from invalid JSON file
        with self.assertRaises(CLIError):
            self.kwargs['json'] = self._get_test_data_file('batch-pool-create-invalid.json').replace('\\', '\\\\')
            self.batch_cmd('batch pool create --json-file {json}')

        # test create pool from JSON file with additional parameters
        with self.assertRaises(SystemExit):
            self.kwargs['json'] = self._get_test_data_file('batch-pool-create.json').replace('\\', '\\\\')
            self.batch_cmd('batch pool create --json-file {json} --vm-size small')

        # test list pools
        pool_list = self.batch_cmd('batch pool list')
        pool_list = pool_list.get_output_in_json()
        self.assertEqual(len(pool_list), 3)
        pool_ids = sorted([p['id'] for p in pool_list])
        self.assertEqual(pool_ids, ["azure-cli-test-iaas", "azure-cli-test-json", "azure-cli-test-paas"])

        # test list pools with select
        pool_list = self.batch_cmd('batch pool list --filter "id eq \'{pool_p}\'"').get_output_in_json()
        self.assertEqual(len(pool_list), 1)

        # test resize pool
        self.batch_cmd('batch pool resize --pool-id {pool_p} --target-dedicated-nodes 5')
        self.batch_cmd('batch pool show --pool-id {pool_p} '
                       '--select "allocationState, targetDedicatedNodes"').assert_with_checks([
                           self.check('allocationState', 'resizing'),
                           self.check('targetDedicatedNodes', 5)])

        # test cancel pool resize
        self.batch_cmd('batch pool resize --pool-id {pool_p} --abort')

        # test enable autoscale
        self.batch_cmd('batch pool autoscale enable --pool-id {pool_i} '
                       '--auto-scale-formula "$TargetDedicatedNodes=3"')
        self.batch_cmd('batch pool show --pool-id {pool_i} --select "enableAutoScale"').assert_with_checks([
            self.check('enableAutoScale', True)])

        # test evaluate autoscale
        self.batch_cmd('batch pool autoscale evaluate --pool-id {pool_i} '
                       '--auto-scale-formula "$TargetDedicatedNodes=3"')

        # test disable autoscale
        self.batch_cmd('batch pool autoscale disable --pool-id {pool_i}')
        self.batch_cmd('batch pool show --pool-id {pool_i} --select "enableAutoScale"').assert_with_checks([
            self.check('enableAutoScale', False)])

        # test list usage metrics
        self.batch_cmd('batch pool usage-metrics list')

        # TODO: Test update pool from JSON file

        # test patch pool using parameters
        current = self.batch_cmd('batch pool show --pool-id {pool_j} --select "startTask"').get_output_in_json()
        self.batch_cmd('batch pool set --pool-id {pool_j} --start-task-command-line new_value')
        updated = self.batch_cmd('batch pool show --pool-id {pool_j} --select "startTask"').get_output_in_json()
        self.assertNotEqual(current['startTask']['commandLine'], updated['startTask']['commandLine'])

        # test list node agent skus
        self.batch_cmd('batch pool supported-images list')

        # test delete iaas pool
        self.batch_cmd('batch pool delete --pool-id {pool_i} --yes')
        self.batch_cmd('batch pool show --pool-id {pool_i} --select "state"').assert_with_checks([
            self.check('state', 'deleting')])

        # test app package reference
        self.batch_cmd('batch pool create --id app_package_test --vm-size small --os-family 4 '
                       '--application-package-references does-not-exist', expect_failure=True)
        self.batch_cmd('batch pool set --pool-id {pool_p} --application-package-references does-not-exist',
                       expect_failure=True)

        # TODO: Test node commands
