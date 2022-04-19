#!/usr/bin/env python

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import logging
import subprocess
import sys
from azdev.utilities import get_path_table

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)

matrix_cnt, matrix_idx = [int(i) for i in sys.argv[1].split('_')]
profile = sys.argv[2]
serial_modules = sys.argv[3].split()
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


class AutomaticScheduling(object):

    def __init__(self):
        """
        self.jobs: Record the test time of each module
        self.modules: All modules and core, ignore extensions
        self.serial_modules: All modules which need to execute in serial mode
        self.works: Record which modules each worker needs to test
        self.matrix_cnt:
        The total number of concurrent automation full test pipeline job with specify python version
        Best practice is to keep the number of concurrent tasks below 50, so we set matrix_cnt = 10
        Total concurrent number: AutomationTest20200901 * 3 + AutomationTest20190301 * 3 + AutomationTest20180301 * 3 + AutomationFullTest * 10 * 3 (python_version) = 39
        self.matrix_idx:
        The index of concurrent automation full test pipeline job with specify python version
        """
        self.jobs = []
        self.modules = {}
        self.serial_modules = serial_modules
        self.works = []
        self.matrix_cnt = matrix_cnt
        self.matrix_idx = matrix_idx
        for i in range(self.matrix_cnt):
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

    def get_matrix_modules(self):
        # get modules which need to execute in the pipeline with specific matrix index
        for k, v in self.jobs:
            idx = self.get_worker()
            self.works[idx][k] = v
        # matrix_idx: 1~n, python list index: 0~n-1
        self.matrix_idx -= 1
        return self.works[self.matrix_idx]

    def run_matrix_modules(self, parallel_modules):
        # divide matrix modules into parallel or serial execution
        error_flag = False
        serial_tests = []
        parallel_tests = []
        for k, v in parallel_modules.items():
            if k in self.serial_modules:
                serial_tests.append(k)
            else:
                parallel_tests.append(k)
        if serial_tests:
            cmd = ['azdev', 'test', '--no-exitfirst', '--verbose', '--series'] + \
                  serial_tests + ['--profile', f'{profile}', '--pytest-args', '"--durations=0"']
            logger.info(cmd)
            try:
                subprocess.run(cmd)
            except subprocess.CalledProcessError:
                error_flag = True
        if parallel_tests:
            cmd = ['azdev', 'test', '--no-exitfirst', '--verbose'] + \
                  parallel_tests + ['--profile', f'{profile}', '--pytest-args', '"--durations=0"']
            logger.info(cmd)
            try:
                subprocess.run(cmd)
            except subprocess.CalledProcessError:
                error_flag = True
        return error_flag


def main():
    logger.info("Start automation full test ...\n")
    autoschduling = AutomaticScheduling()
    autoschduling.get_all_modules()
    autoschduling.append_new_modules()
    parallel_modules = autoschduling.get_matrix_modules()
    sys.exit(1) if autoschduling.run_matrix_modules(parallel_modules) else sys.exit(0)


if __name__ == '__main__':
    main()
