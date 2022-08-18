#!/usr/bin/env python

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import logging
import os
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from azdev.utilities import get_path_table

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)

# sys.argv is passed by
# .azure-pipelines/templates/automation_test.yml in section `Running full test`
# scripts/bump_version/bump_version.yml in `azdev test` step
instance_cnt = int(sys.argv[1])
instance_idx = int(sys.argv[2])
profile = sys.argv[3]
serial_modules = sys.argv[4].split()
fix_failure_tests = sys.argv[5].lower() == 'true' if len(sys.argv) >= 6 else False
working_directory = "/home/vsts/work/1/s"
azdev_test_result_dir = "/home/vsts/.azdev/env_config/home/vsts/work/1/s/env"
jobs = {
            'acr': 45,
            'acs': 62,
            'advisor': 18,
            'ams': 136,
            'apim': 30,
            'appconfig': 41,
            'appservice': 150,  # series
            # 'appservice': 157,  # parallel
            'aro': 33,
            'backup': 76,
            'batch': 21,
            'batchai': 24,
            'billing': 21,
            'botservice': 25,  # series
            # 'botservice': 28,  # parallel
            'cdn': 36,
            'cloud': 18,  # series
            # 'cloud': 22,  # parallel
            'cognitiveservices': 24,
            'config': 21,
            'configure': 17,
            'consumption': 21,
            'container': 19,
            'cosmosdb': 45,
            'databoxedge': 25,
            'deploymentmanager': 18,
            'dla': 19,
            'dls': 22,
            'dms': 22,
            'eventgrid': 24,
            'eventhubs': 24,
            'extension': 0,
            'feedback': 31,
            'find': 22,
            'hdinsight': 34,
            'identity': 18,
            'interactive': 18,
            'iot': 57,
            'keyvault': 39,
            'kusto': 23,
            'lab': 19,
            'managedservices': 18,
            'maps': 19,
            'marketplaceordering': 18,
            'monitor': 66,
            'natgateway': 22,
            'netappfiles': 48,
            'network': 364,  # series
            # 'network': 182,  # parallel
            'policyinsights': 20,
            'privatedns': 29,
            'profile': 20,
            'rdbms': 89,
            'redis': 31,
            'relay': 22,
            'reservations': 20,
            'resource': 101,
            'role': 38,
            'search': 34,
            'security': 23,
            'servicebus': 24,
            'serviceconnector': 56,
            'servicefabric': 49,
            'signalr': 20,
            'sql': 117,
            'sqlvm': 31,
            'storage': 108,
            'synapse': 45,
            'util': 18,
            'vm': 313,
            'azure-cli': 16,
            'azure-cli-core': 26,
            'azure-cli-telemetry': 18,
            'azure-cli-testsdk': 20,
        }


def run_command(cmd, check_return_code=False):
    error_flag = False
    logger.info(cmd)
    try:
        out = subprocess.run(cmd, check=True)
        if check_return_code and out.returncode:
            raise RuntimeError(f"{cmd} failed")
    except subprocess.CalledProcessError:
        error_flag = True
    return error_flag


def git_restore(file_path):
    if not file_path:
        return
    logger.info(f"git restore {file_path}")
    out = subprocess.Popen(["git", "restore", file_path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    stdout, err = out.communicate()
    if stdout:
        logger.info(stdout)
    if err:
        logger.warning(err)


def git_push(message):
    out = subprocess.Popen(["git", "status"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    stdout, _ = out.communicate()
    if "nothing to commit, working tree clean" in str(stdout):
        return
    try:
        run_command(["git", "add", "*/command_modules/*"], check_return_code=True)
        run_command(["git", "commit", "-m", message], check_return_code=True)
    except RuntimeError as ex:
        raise ex
    retry = 3
    while retry >= 0:
        try:
            run_command(["git", "fetch", "azclibot"], check_return_code=True)
            run_command(["git", "pull", "--rebase"], check_return_code=True)
            run_command(["git", "push"], check_return_code=True)

            logger.info("git push all recording files")
            break
        except RuntimeError as ex:
            if retry == 0:
                raise ex
            retry -= 1
            time.sleep(10)


def get_failed_tests(test_result_fp):
    tree = ET.parse(test_result_fp)
    root = tree.getroot()
    failed_tests = {}
    for testsuite in root:
        for testcase in testsuite:
            # Collect failed tests
            failures = testcase.findall('failure')
            if failures:
                logger.info(f"failed testcase attributes: {testcase.attrib}")
                test_case = testcase.attrib['name']
                recording_folder = os.path.join(os.path.dirname(testcase.attrib['file']), 'recordings')
                if 'src' not in recording_folder:
                    recording_folder = os.path.join(os.path.join('src', 'azure-cli'), recording_folder)
                failed_tests[test_case] = os.path.join(recording_folder, test_case + '.yaml')
    return failed_tests


def process_test(cmd, azdev_test_result_fp, live_rerun=False):
    error_flag = run_command(cmd)
    if not error_flag or not live_rerun:
        return error_flag
    # drop the original `--pytest-args` and add new arguments
    cmd = cmd[:-2] + ['--lf', '--live', '--pytest-args', '-o junit_family=xunit1']
    error_flag = run_command(cmd)
    # restore original recording yaml file for failed test in live run
    if error_flag:
        failed_tests = get_failed_tests(azdev_test_result_fp)
        for (test, file) in failed_tests.items():
            git_restore(os.path.join(working_directory, file))

    # save live run recording changes to git
    commit_message = f"Rerun tests from instance {instance_idx}. See {os.path.basename(azdev_test_result_fp)} for details"
    git_push(commit_message)
    return False


class AutomaticScheduling(object):

    def __init__(self):
        """
        self.jobs: Record the test time of each module
        self.modules: All modules and core, ignore extensions
        self.serial_modules: All modules which need to execute in serial mode
        self.works: Record which modules each worker needs to test
        self.instance_cnt:
        The total number of concurrent automation full test pipeline instance with specify python version
        Because we share the vm pool with azure-sdk team, so we can't set the number of concurrency arbitrarily
        Best practice is to keep the number of concurrent tasks below 50
        If you set a larger number of concurrency, it will cause many instances to be in the waiting state
        And the network module has the largest number of test cases and can only be tested serially for now, so setting instance_cnt = 8 is sufficient
        Total concurrent number: AutomationTest20200901 * 3 + AutomationTest20190301 * 3 + AutomationTest20180301 * 3 + AutomationFullTest * 8 * 3 (python_version) = 33
        self.instance_idx:
        The index of concurrent automation full test pipeline instance with specify python version
        For example:
        instance_cnt = 8, instance_idx = 3: means we have 8 instances totally, and now we are scheduling modules on third instance
        instance_cnt = 1, instance_idx = 1: means we only have 1 instance, so we don't need to schedule modules
        """
        self.jobs = []
        self.modules = {}
        self.serial_modules = serial_modules
        self.works = []
        self.instance_cnt = instance_cnt
        self.instance_idx = instance_idx
        for i in range(self.instance_cnt):
            worker = {}
            self.works.append(worker)
        self.profile = profile

    def get_all_modules(self):
        result = get_path_table()
        # only get modules and core, ignore extensions
        self.modules = {**result['mod'], **result['core']}

    def append_new_modules(self):
        # If add a new module, use average test time
        avg_cost = int(sum(jobs.values()) / len(jobs.values()))
        for module in self.modules:
            if module not in jobs.keys():
                jobs[module] = avg_cost
        # sort jobs by time cost (desc)
        self.jobs = sorted(jobs.items(), key=lambda item: -item[1])

    def get_worker(self):
        """
        Use greedy algorithm distribute jobs to each worker
        For each job, we assign it to the worker with the fewest jobs currently
        :return worker number
        """
        for idx, worker in enumerate(self.works):
            tmp_time = sum(worker.values()) if sum(worker.values()) else 0
            if idx == 0:
                worker_time = tmp_time
                worker_num = idx
            if tmp_time < worker_time:
                worker_time = tmp_time
                worker_num = idx
        return worker_num

    def get_instance_modules(self):
        # get modules which need to execute in the pipeline instance with specific index
        for k, v in self.jobs:
            idx = self.get_worker()
            self.works[idx][k] = v
        # instance_idx: 1~n, python list index: 0~n-1
        self.instance_idx -= 1
        return self.works[self.instance_idx]

    def run_instance_modules(self, instance_modules):
        # divide the modules that the current instance needs to execute into parallel or serial execution
        error_flag = False
        serial_tests = []
        parallel_tests = []
        for k, v in instance_modules.items():
            if k in self.serial_modules:
                serial_tests.append(k)
            else:
                parallel_tests.append(k)
        if serial_tests:
            azdev_test_result_fp = os.path.join(azdev_test_result_dir, f"test_results_{instance_idx}.serial.xml")
            cmd = ['azdev', 'test', '--no-exitfirst', '--verbose', '--series'] + serial_tests + \
                  ['--profile', f'{profile}', '--xml-path', azdev_test_result_fp, '--pytest-args', '"--durations=10"']
            error_flag = process_test(cmd, azdev_test_result_fp, live_rerun=fix_failure_tests)
        if parallel_tests:
            azdev_test_result_fp = os.path.join(azdev_test_result_dir, f"test_results_{instance_idx}.parallel.xml")
            cmd = ['azdev', 'test', '--no-exitfirst', '--verbose'] + parallel_tests + \
                  ['--profile', f'{profile}', '--xml-path', azdev_test_result_fp, '--pytest-args', '"--durations=10"']
            error_flag = process_test(cmd, azdev_test_result_fp, live_rerun=fix_failure_tests)
        return error_flag


def main():
    logger.info("Start automation full test ...\n")
    autoscheduling = AutomaticScheduling()
    autoscheduling.get_all_modules()
    autoscheduling.append_new_modules()
    instance_modules = autoscheduling.get_instance_modules()
    sys.exit(1) if autoscheduling.run_instance_modules(instance_modules) else sys.exit(0)


if __name__ == '__main__':
    main()
