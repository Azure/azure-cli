#!/usr/bin/env python

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import subprocess
import sys
from pprint import pprint

# TODO new module not in jobs

# Automation full test
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
    # 'extension': 37,
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
    'azure-cli-core': 26,
    'azure-cli-testsdk': 20,
    'azure-cli': 16,
    'azure-cli-telemetry': 18,
 }
series_modules = []
# series_modules = ['appservice', 'botservice', 'cloud', 'network']
part, part_idx = [int(i) for i in sys.argv[1].split('_')]
parallel, para_idx = [int(i) for i in sys.argv[2].split('_')]
profile = sys.argv[3]

jobs = sorted(jobs.items(), key=lambda item:-item[1])
# pprint(jobs)
# pprint(len(jobs))

works = []
for i in range(parallel):
    worker = {}
    works.append(worker)


def get_worker():
    for idx, worker in enumerate(works):
        tmp_time = sum(worker.values()) if sum(worker.values()) else 0
        if idx == 0:
            worker_time = tmp_time
            worker_num = idx
        if tmp_time < worker_time:
            worker_time = tmp_time
            worker_num = idx
    return worker_num


def get_part_modules(part, part_idx):
    part_modules = []
    part_idx -= 1
    while part_idx < len(jobs):
        part_modules.append(jobs[part_idx])
        part_idx += part
    # pprint(part_modules)
    # pprint(len(part_modules))
    return part_modules


def get_paraller_modules(part_modules, para_idx):
    for k, v in part_modules:
        idx = get_worker()
        works[idx][k] = v
    # pprint(works)
    pprint(para_idx)
    para_idx -= 1
    return works[para_idx]


def run_paraller_modules(paraller_modules, profile):
    series = []
    parallers = []
    for k, v in paraller_modules.items():
        if k in series_modules:
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


part_modules = get_part_modules(part, part_idx)
para_modules = get_paraller_modules(part_modules, para_idx)
run_paraller_modules(para_modules, profile)


# if __name__ == '__main__':
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


