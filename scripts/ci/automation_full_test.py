#!/usr/bin/env python

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import subprocess
import sys
from pprint import pprint
from azdev.utilities import get_path_table


# part, part_idx = 1, 1
# parallel, para_idx = 8, 1
# profile = 'latest'
part, part_idx = [int(i) for i in sys.argv[1].split('_')]
parallel, para_idx = [int(i) for i in sys.argv[2].split('_')]
profile = sys.argv[3]

jobs = {
            'acr': 45,
            'acs': 62,
            'advisor': 18,
            'ams': 136,
            'apim': 30,
            'appconfig': 41,
            # 'appservice': 150,  # series
            'appservice': 157,  # paraller
            'aro': 33,
            'backup': 76,
            'batch': 21,
            'batchai': 24,
            'billing': 21,
            # 'botservice': 25,  # series
            'botservice': 28,  # paraller
            'cdn': 36,
            # 'cloud': 18,  # series
            'cloud': 22,  # paraller
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
            # 'network': 322,  # paraller
            'network': 182,  # series
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
            'vm': 271,
            'azure-cli': 16,
            'azure-cli-core': 26,
            'azure-cli-telemetry': 18,
            'azure-cli-testsdk': 20,
        }


class AutomaticScheduling(object):

    def __init__(self):
        self.jobs = []
        self.modules = []
        self.series_modules = []
        # series_modules = ['appservice', 'botservice', 'cloud', 'network']
        self.works = []
        for i in range(parallel):
            worker = {}
            self.works.append(worker)
        self.part = part
        self.part_idx = part_idx
        self.parallel = parallel
        self.para_idx = part_idx
        self.profile = profile

    def get_all_modules(self):
        result = get_path_table()
        self.modules = {**result['mod'], **result['core']}

    def append_new_modules(self):
        avg_cost = int(sum(jobs.values()) / len(jobs.values()))
        for module in self.modules:
            if module not in jobs.keys():
                jobs[module] = avg_cost
        self.jobs = sorted(jobs.items(), key=lambda item: -item[1])

    def get_worker(self):
        for idx, worker in enumerate(self.works):
            tmp_time = sum(worker.values()) if sum(worker.values()) else 0
            if idx == 0:
                worker_time = tmp_time
                worker_num = idx
            if tmp_time < worker_time:
                worker_time = tmp_time
                worker_num = idx
        return worker_num

    def get_part_modules(self):
        part_modules = []
        self.part_idx -= 1
        while self.part_idx < len(self.jobs):
            part_modules.append(self.jobs[self.part_idx])
            self.part_idx += self.part
        # pprint(part_modules)
        # pprint(len(part_modules))
        return part_modules

    def get_paraller_modules(self, part_modules):
        for k, v in part_modules:
            idx = self.get_worker()
            self.works[idx][k] = v
        pprint(self.works)
        pprint(self.para_idx)
        self.para_idx -= 1
        return self.works[self.para_idx]

    def run_paraller_modules(self, paraller_modules):
        series = []
        parallers = []
        for k, v in paraller_modules.items():
            if k in self.series_modules:
                series.append(k)
            else:
                parallers.append(k)
        if series:
            cmd = ['azdev', 'test', '--no-exitfirst', '--verbose', '--series'] + series + ['--profile', f'{profile}', '--pytest-args', '"--durations=0"']
            print(cmd)
            subprocess.call(cmd)
        if parallers:
            cmd = ['azdev', 'test', '--no-exitfirst', '--verbose'] + parallers + ['--profile', f'{profile}', '--pytest-args', '"--durations=0"']
            print(cmd)
            subprocess.call(cmd)


AS = AutomaticScheduling()
AS.get_all_modules()
AS.append_new_modules()
part_modules = AS.get_part_modules()
para_modules = AS.get_paraller_modules(part_modules)
AS.run_paraller_modules(para_modules)


if __name__ == '__main__':
    pass
    # works = []
    # for i in range(8):
    #     worker = {}
    #     works.append(worker)
    # part, part_idx = [int(i) for i in '1_1'.split('_')]
    # parallel, para_idx = [int(i) for i in '8_1'.split('_')]
    # profile = 'latest'
    # part_modules = get_part_modules(part, part_idx)
    # para_modules = get_paraller_modules(part_modules, para_idx)
    # pprint(works)
    # run_paraller_modules(para_modules, profile)
    # works = []
    # for i in range(8):
    #     worker = {}
    #     works.append(worker)
    # part, part_idx = [int(i) for i in '4_1'.split('_')]
    # parallel, para_idx = [int(i) for i in '8_2'.split('_')]
    # profile = 'latest'
    # part_modules = get_part_modules(part, part_idx)
    # para_modules = get_paraller_modules(part_modules, para_idx)
    # run_paraller_modules(para_modules, profile)
    # works = []
    # for i in range(8):
    #     worker = {}
    #     works.append(worker)
    # part, part_idx = [int(i) for i in '4_1'.split('_')]
    # parallel, para_idx = [int(i) for i in '8_3'.split('_')]
    # profile = 'latest'
    # part_modules = get_part_modules(part, part_idx)
    # para_modules = get_paraller_modules(part_modules, para_idx)
    # run_paraller_modules(para_modules, profile)
    # works = []
    # for i in range(8):
    #     worker = {}
    #     works.append(worker)
    # part, part_idx = [int(i) for i in '4_1'.split('_')]
    # parallel, para_idx = [int(i) for i in '8_4'.split('_')]
    # profile = 'latest'
    # part_modules = get_part_modules(part, part_idx)
    # para_modules = get_paraller_modules(part_modules, para_idx)
    # run_paraller_modules(para_modules, profile)
    # works = []
    # for i in range(8):
    #     worker = {}
    #     works.append(worker)
    # part, part_idx = [int(i) for i in '4_1'.split('_')]
    # parallel, para_idx = [int(i) for i in '8_5'.split('_')]
    # profile = 'latest'
    # part_modules = get_part_modules(part, part_idx)
    # para_modules = get_paraller_modules(part_modules, para_idx)
    # run_paraller_modules(para_modules, profile)
    # works = []
    # for i in range(8):
    #     worker = {}
    #     works.append(worker)
    # part, part_idx = [int(i) for i in '4_1'.split('_')]
    # parallel, para_idx = [int(i) for i in '8_6'.split('_')]
    # profile = 'latest'
    # part_modules = get_part_modules(part, part_idx)
    # para_modules = get_paraller_modules(part_modules, para_idx)
    # run_paraller_modules(para_modules, profile)
    # works = []
    # for i in range(8):
    #     worker = {}
    #     works.append(worker)
    # part, part_idx = [int(i) for i in '4_1'.split('_')]
    # parallel, para_idx = [int(i) for i in '8_7'.split('_')]
    # profile = 'latest'
    # part_modules = get_part_modules(part, part_idx)
    # para_modules = get_paraller_modules(part_modules, para_idx)
    # run_paraller_modules(para_modules, profile)
    # works = []
    # for i in range(8):
    #     worker = {}
    #     works.append(worker)
    # part, part_idx = [int(i) for i in '4_1'.split('_')]
    # parallel, para_idx = [int(i) for i in '8_8'.split('_')]
    # profile = 'latest'
    # part_modules = get_part_modules(part, part_idx)
    # para_modules = get_paraller_modules(part_modules, para_idx)
    # run_paraller_modules(para_modules, profile)

    # part, part_idx = [int(i) for i in '4_1'.split('_')]
    # part_modules = get_part(part, part_idx)
    # part, part_idx = [int(i) for i in '4_2'.split('_')]
    # part_modules = get_part(part, part_idx)
    # part, part_idx = [int(i) for i in '4_3'.split('_')]
    # part_modules = get_part(part, part_idx)
    # part, part_idx = [int(i) for i in '4_4'.split('_')]
    # part_modules = get_part(part, part_idx)


