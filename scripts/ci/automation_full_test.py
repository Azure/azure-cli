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

parallel, para_idx = [int(i) for i in sys.argv[1].split('_')]
profile = sys.argv[2]

jobs = {
            'acr': 45,
            'acs': 62,
            'advisor': 18,
            'ams': 136,
            'apim': 30,
            'appconfig': 41,
            'appservice': 150,  # series
            # 'appservice': 157,  # paraller
            'aro': 33,
            'backup': 76,
            'batch': 21,
            'batchai': 24,
            'billing': 21,
            'botservice': 25,  # series
            # 'botservice': 28,  # paraller
            'cdn': 36,
            'cloud': 18,  # series
            # 'cloud': 22,  # paraller
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
            # 'network': 182,  # paraller
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
        self.jobs = []
        self.modules = {}
        self.series_modules = ['appservice', 'botservice', 'cloud', 'network', 'azure-cli-core', 'azure-cli-telemetry']
        self.works = []
        for i in range(parallel):
            worker = {}
            self.works.append(worker)
        self.parallel = parallel
        self.para_idx = para_idx
        self.profile = profile

    def get_all_modules(self):
        result = get_path_table()
        # only get modules and core, ignore extensions
        self.modules = {**result['mod'], **result['core']}

    def append_new_modules(self):
        # if add a new module, use average test time
        avg_cost = int(sum(jobs.values()) / len(jobs.values()))
        for module in self.modules:
            if module not in jobs.keys():
                jobs[module] = avg_cost
        self.jobs = sorted(jobs.items(), key=lambda item: -item[1])

    def get_worker(self):
        # distribute jobs equally to each worker
        for idx, worker in enumerate(self.works):
            tmp_time = sum(worker.values()) if sum(worker.values()) else 0
            if idx == 0:
                worker_time = tmp_time
                worker_num = idx
            if tmp_time < worker_time:
                worker_time = tmp_time
                worker_num = idx
        return worker_num

    def get_paraller_modules(self):
        for k, v in self.jobs:
            idx = self.get_worker()
            self.works[idx][k] = v
        # para_idx: 1~n, python list index: 0~n-1
        self.para_idx -= 1
        return self.works[self.para_idx]

    def run_paraller_modules(self, paraller_modules):
        # divide all modules into parallel or serial execution
        error_flag = False
        series = []
        parallers = []
        for k, v in paraller_modules.items():
            if k in self.series_modules:
                series.append(k)
            else:
                parallers.append(k)
        if series:
            cmd = ['azdev', 'test', '--no-exitfirst', '--verbose', '--series'] + \
                  series + ['--profile', f'{profile}', '--pytest-args', '"--durations=0"']
            logger.info(cmd)
            try:
                subprocess.run(cmd)
            except subprocess.CalledProcessError:
                error_flag = True
        if parallers:
            cmd = ['azdev', 'test', '--no-exitfirst', '--verbose'] + \
                  parallers + ['--profile', f'{profile}', '--pytest-args', '"--durations=0"']
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
    para_modules = autoschduling.get_paraller_modules()
    sys.exit(1) if autoschduling.run_paraller_modules(para_modules) else sys.exit(0)


if __name__ == '__main__':
    main()
