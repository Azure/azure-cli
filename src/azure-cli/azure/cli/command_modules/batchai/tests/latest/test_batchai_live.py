# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import os
import time

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, live_only
from azure.cli.testsdk import JMESPathCheck

LOCATION_FOR_LIVE_TESTS = 'northeurope'


def _data_file(filename):
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', filename).replace('\\', '\\\\')


@live_only()
class BatchAILiveScenariosTests(ScenarioTest):
    @ResourceGroupPreparer(location=LOCATION_FOR_LIVE_TESTS)
    def test_cluster_job_node_exec(self, resource_group):
        self.cmd('batchai workspace create -g {0} -n workspace'.format(resource_group))
        self.cmd('batchai experiment create -g {0} -w workspace -n experiment'.format(resource_group))

        # Create a cluster to test the ssh connection
        self.cmd('batchai cluster create -g {0} -w workspace -n simple -s Standard_D1 -t 1 '
                 '-u alex --generate-ssh-keys'.format(resource_group))

        # Schedule a job to know when the cluster is ready
        self.cmd('batchai job create -g {0} -w workspace -e experiment -n nop -c simple -f {1}'.format(
            resource_group, _data_file('nop_job.json')))
        self.cmd('batchai job wait -g {0} -w workspace -e experiment -n nop'.format(resource_group))

        # Submit a job which waits on a port 9000
        self.cmd('batchai job create -g {0} -w workspace -e experiment -n waiter1 -c simple -f {1}'.format(
            resource_group, _data_file('job_waiting_on_port.json')))

        # Give the service some time to actually start the job
        time.sleep(30)

        # The job should be in running state
        self.cmd('batchai job show -g {0} -w workspace -e experiment -n waiter1'.format(
            resource_group), checks=[JMESPathCheck('executionState', 'running')])

        # Write to port 9000 on the node
        self.cmd('batchai cluster node exec -g {0} -w workspace -c simple --exec "echo hi | nc localhost 9000"'.format(
            resource_group))

        # The job must success soon
        self.cmd('batchai job wait -g {0} -w workspace -e experiment -n waiter1'.format(resource_group))

        # Check the same but using 'job node exec'
        self.cmd('batchai job create -g {0} -w workspace -e experiment -n waiter2 -c simple -f {1}'.format(
            resource_group, _data_file('job_waiting_on_port.json')))
        time.sleep(30)
        self.cmd('batchai job node exec -g {0} -w workspace -e experiment -j waiter2 '
                 '--exec "echo hi | nc localhost 9000"'.format(resource_group))
        self.cmd('batchai job wait -g {0} -w workspace -e experiment -n waiter2'.format(resource_group))
