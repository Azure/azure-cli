# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import datetime
import os

from azure.cli.core._util import CLIError
from azure.cli.command_modules.batch.tests.test_batch_data_plane_command_base import (
    BatchDataPlaneTestBase)


class BatchJobTest(BatchDataPlaneTestBase):

    def __init__(self, test_method):
        super(BatchJobTest, self).__init__(__file__, test_method)
        self.pool_paas = "azure-cli-test-paas"
        self.job1 = "cli-test-job-1"
        self.data_dir = os.path.join(
            os.path.dirname(__file__), 'data', 'batch-job-{}.json').replace('\\', '\\\\')

    def tear_down(self):
        # Clean up any running pools in case the test exited early
        try:
            self.cmd('batch pool delete --pool-id {} --yes'.format(self.pool_paas))
        except Exception:  # pylint: disable=broad-except
            pass
        try:
            self.cmd('batch job delete --job-id {} --yes'.format(self.job1))
        except Exception:  # pylint: disable=broad-except
            pass

    def test_batch_jobs(self):
        self.execute()

    def body(self):
        # pylint: disable=too-many-statements
        # test create paas pool using parameters
        self.cmd('batch pool create --id {} --vm-size small --os-family 4'.format(
            self.pool_paas))

        start_time = datetime.datetime.now().isoformat()
        # test create job with missing parameters
        with self.assertRaises(SystemExit):
            self.cmd('batch job create --id {} --metadata test=value '
                     '--job-manager-task-environment-settings a=b '
                     '--job-max-task-retry-count 5 '.format(self.job1))

        # test create job
        self.cmd('batch job create --id {} --metadata test=value --job-max-task-retry-count 5 '
                 '--job-manager-task-id JobManager '
                 '--job-manager-task-command-line "cmd /c set AZ_BATCH_TASK_ID" '
                 '--job-manager-task-environment-settings '
                 'CLI_TEST_VAR=CLI_TEST_VAR_VALUE --pool-id {}'.format(self.job1, self.pool_paas))

        # test get job
        job1 = self.cmd('batch job show --job-id {}'.format(self.job1))
        self.assertEqual(job1['metadata'][0]['name'], 'test')
        self.assertEqual(job1['metadata'][0]['value'], 'value')
        self.assertEqual(job1['jobManagerTask']['environmentSettings'][0]['name'],
                         'CLI_TEST_VAR')
        self.assertEqual(job1['jobManagerTask']['environmentSettings'][0]['value'],
                         'CLI_TEST_VAR_VALUE')
        self.assertEqual(job1['jobManagerTask']['id'], 'JobManager')
        self.assertEqual(job1['constraints']['maxTaskRetryCount'], 5)
        self.assertEqual(job1['onAllTasksComplete'], 'noAction')

        # test bad enum value
        with self.assertRaises(SystemExit):
            self.cmd('batch job set --job-id {} '
                     '--on-all-tasks-complete badValue '.format(self.job1))

        # test patch job
        self.cmd('batch job set --job-id {} --job-max-wall-clock-time P3Y6M4DT12H30M5S '
                 '--on-all-tasks-complete terminateJob'.format(self.job1))
        job1 = self.cmd('batch job show --job-id {}'.format(self.job1))
        self.assertEqual(job1['metadata'][0]['name'], 'test')
        self.assertEqual(job1['metadata'][0]['value'], 'value')
        self.assertEqual(job1['jobManagerTask']['environmentSettings'][0]['name'],
                         'CLI_TEST_VAR')
        self.assertEqual(job1['jobManagerTask']['environmentSettings'][0]['value'],
                         'CLI_TEST_VAR_VALUE')
        self.assertEqual(job1['jobManagerTask']['id'], 'JobManager')
        self.assertEqual(job1['constraints']['maxTaskRetryCount'], 0)
        self.assertEqual(job1['constraints']['maxWallClockTime'], '1279 days, 12:30:05')
        self.assertEqual(job1['onAllTasksComplete'], 'terminateJob')

        # test filter/header argument
        with self.assertRaises(CLIError):
            self.cmd('batch job reset --job-id {} --pool-id {} '
                     '--on-all-tasks-complete terminateJob '
                     '--if-unmodified-since {}'.format(self.job1, self.pool_paas, start_time))

        # test reset job
        self.cmd('batch job reset --job-id {} --pool-id {}  '
                 '--on-all-tasks-complete terminateJob '.format(self.job1, self.pool_paas))
        job1 = self.cmd('batch job show --job-id {}'.format(self.job1))
        self.assertEqual(job1['metadata'], None)
        self.assertEqual(job1['constraints']['maxTaskRetryCount'], 0)
        self.assertNotEqual(job1['constraints']['maxWallClockTime'], '1279 days, 12:30:05')
