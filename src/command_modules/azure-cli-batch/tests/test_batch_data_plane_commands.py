# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os

from azure.cli.testsdk.vcr_test_base import (JMESPathCheck)
from .test_batch_data_plane_command_base import (BatchDataPlaneTestBase)


class BatchCertificateScenarioTest(BatchDataPlaneTestBase):

    def __init__(self, test_method):
        super(BatchCertificateScenarioTest, self).__init__(__file__, test_method)
        self.create_cert_file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                  'data',
                                                  'batchtest.cer')
        self.cert_thumbprint = '59833fd835f827e9ec693a4c82435a6360cc6271'

    def test_batch_certificate_cmd(self):
        self.execute()

    def body(self):
        # test create certificate with default set
        self.cmd('batch certificate create --thumbprint {} --certificate-file "{}"'.
                 format(self.cert_thumbprint, self.create_cert_file_path),
                 checks=[
                     JMESPathCheck('thumbprint', self.cert_thumbprint),
                     JMESPathCheck('thumbprintAlgorithm', 'sha1'),
                     JMESPathCheck('state', 'active')
                 ])

        # test create account with default set
        self.cmd('batch certificate list', checks=[
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].thumbprint', self.cert_thumbprint),
        ])

        self.cmd("batch certificate delete --thumbprint {} --yes".
                 format(self.cert_thumbprint))

        self.cmd('batch certificate show --thumbprint {}'.
                 format(self.cert_thumbprint),
                 checks=[
                     JMESPathCheck('thumbprint', self.cert_thumbprint),
                     JMESPathCheck('thumbprintAlgorithm', 'sha1'),
                     JMESPathCheck('state', 'deleting')
                 ])


class BatchPoolScenarioTest(BatchDataPlaneTestBase):

    def __init__(self, test_method):
        super(BatchPoolScenarioTest, self).__init__(__file__, test_method)
        self.create_pool_file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                  'data',
                                                  'batchCreatePool.json')
        self.update_pool_file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                  'data',
                                                  'batchUpdatePool.json')
        self.share_pool_id = 'xplatTestPool'
        self.create_pool_id = 'xplatCreatedPool'

    def test_batch_pool_cmd(self):
        self.execute()

    def body(self):
        result = self.cmd('batch pool show --pool-id {}'.format(self.share_pool_id),
                          checks=[JMESPathCheck('allocationState', 'steady'),
                                  JMESPathCheck('id', self.share_pool_id)])
        target = result['currentDedicated']

        self.cmd('batch pool resize --pool-id {} --target-dedicated 5'.format(self.share_pool_id))

        self.cmd('batch pool show --pool-id {}'.format(self.share_pool_id),
                 checks=[JMESPathCheck('allocationState', 'resizing'),
                         JMESPathCheck('targetDedicated', 5),
                         JMESPathCheck('id', self.share_pool_id)])

        self.cmd('batch pool resize --pool-id {} --abort'.format(self.share_pool_id))

        if not self.playback:
            import time
            time.sleep(60)

        self.cmd('batch pool show --pool-id {}'.format(self.share_pool_id),
                 checks=[JMESPathCheck('allocationState', 'steady'),
                         JMESPathCheck('id', self.share_pool_id),
                         JMESPathCheck('currentDedicated', target),
                         JMESPathCheck('targetDedicated', 5)])

        self.cmd('batch pool create --json-file "{}"'.format(self.create_pool_file_path))

        self.cmd('batch pool show --pool-id {}'.format(self.create_pool_id),
                 checks=[JMESPathCheck('allocationState', 'steady'),
                         JMESPathCheck('id', self.create_pool_id),
                         JMESPathCheck('startTask.commandLine', "cmd /c echo test"),
                         JMESPathCheck('startTask.userIdentity.autoUser.elevationLevel', "admin")])

        self.cmd('batch pool reset --pool-id {} --json-file "{}"'.
                 format(self.create_pool_id, self.update_pool_file_path),
                 checks=[JMESPathCheck('allocationState', 'steady'),
                         JMESPathCheck('id', self.create_pool_id),
                         JMESPathCheck('startTask.commandLine', "cmd /c echo updated")])

        self.cmd('batch pool reset --pool-id {} --start-task-command-line '
                 'hostname --metadata a=b c=d'.format(self.create_pool_id),
                 checks=[JMESPathCheck('allocationState', 'steady'),
                         JMESPathCheck('id', self.create_pool_id),
                         JMESPathCheck('startTask.commandLine', "hostname"),
                         JMESPathCheck('length(metadata)', 2),
                         JMESPathCheck('metadata[0].name', 'a'),
                         JMESPathCheck('metadata[1].value', 'd')])

        self.cmd('batch pool delete --pool-id {} --yes'.format(self.create_pool_id))


class BatchJobListScenarioTest(BatchDataPlaneTestBase):

    def set_up(self):
        self.cmd('batch job-schedule create --json-file "{}"'.
                 format(self.create_jobschedule_file_path))

    def tear_down(self):
        self.cmd('batch job-schedule delete --job-schedule-id {} --yes'.
                 format(self.job_schedule_id))

    def __init__(self, test_method):
        super(BatchJobListScenarioTest, self).__init__(__file__, test_method)
        self.create_jobschedule_file_path = os.path.join(os.path.
                                                         dirname(os.path.realpath(__file__)),
                                                         'data',
                                                         'batchCreateJobScheduleForJobTests.json')
        self.create_job_file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                 'data',
                                                 'batchCreateJob.json')
        self.job_schedule_id = 'xplatJobScheduleJobTests'
        self.create_job_id = 'xplatJob'

    def test_batch_job_list_cmd(self):
        self.execute()

    def body(self):
        self.cmd('batch job create --json-file "{}"'.format(self.create_job_file_path))

        self.cmd('batch job list --job-schedule-id {}'.format(self.job_schedule_id),
                 checks=[JMESPathCheck('length(@)', 1),
                         JMESPathCheck('[0].id', '{}:job-1'.format(self.job_schedule_id))])

        result = self.cmd('batch job list',
                          checks=[JMESPathCheck('length(@)', 2)])
        self.assertIsNotNone(
            [i for i in result if i['id'] == '{}:job-1'.format(self.job_schedule_id)])
        self.assertIsNotNone([i for i in result if i['id'] == self.create_job_id])

        self.cmd('batch job delete --job-id {} --yes'.format(self.create_job_id))


class BatchTaskAddScenarioTest(BatchDataPlaneTestBase):
    # pylint: disable=too-many-instance-attributes
    def set_up(self):
        self.cmd('batch job create --json-file "{}"'.format(self.create_job_file_path))

    def tear_down(self):
        self.cmd('batch job delete --job-id {} --yes'.format(self.job_id))

    def __init__(self, test_method):
        super(BatchTaskAddScenarioTest, self).__init__(__file__, test_method)
        self.create_task_file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                  'data',
                                                  'batchCreateTask.json')
        self.create_tasks_file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                   'data',
                                                   'batchCreateMultiTasks.json')
        self.create_job_file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                 'data',
                                                 'batchCreateJobForTaskTests.json')
        self.job_id = 'xplatJobForTaskTests'
        self.task_id = 'xplatTask'

    def test_batch_task_create_cmd(self):
        self.execute()

    def body(self):
        self.cmd('batch task create --job-id {} --json-file "{}"'.
                 format(self.job_id, self.create_task_file_path),
                 checks=[JMESPathCheck('id', self.task_id),
                         JMESPathCheck('commandLine', 'cmd /c dir /s')])

        task = self.cmd('batch task show --job-id {} --task-id {}'.format(
            self.job_id, self.task_id))
        self.assertEqual(task['userIdentity']['autoUser']['scope'], 'pool')
        self.assertEqual(task['authenticationTokenSettings']['access'][0], 'job')

        self.cmd('batch task delete --job-id {} --task-id {} --yes'.
                 format(self.job_id, self.task_id))

        self.cmd('batch task create --job-id {} --task-id aaa --command-line "echo hello"'.
                 format(self.job_id),
                 checks=[JMESPathCheck('id', 'aaa'),
                         JMESPathCheck('commandLine', 'echo hello')])

        self.cmd('batch task delete --job-id {} --task-id aaa --yes'.format(self.job_id))

        result = self.cmd('batch task create --job-id {} --json-file "{}"'.
                          format(self.job_id, self.create_tasks_file_path),
                          checks=[JMESPathCheck('length(@)', 3)])
        self.assertIsNotNone([i for i in result if i['taskId'] == 'xplatTask1'])
