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
    'acr': 55,
    'acs': 85,
    'advisor': 40,
    'ams': 162,
    'apim': 87,
    'appconfig': 63,
    'appservice': 132,  # series
    'aro': 62,
    'backup': 138,
    'batch': 48,
    'batchai': 49,
    'billing': 42,
    'botservice': 24,  # series
    'cdn': 58,
    'cloud': 19,  # series
    'cognitiveservices': 63,
    'config': 46,
    'configure': 40,
    'consumption': 43,
    'container': 45,
    'cosmosdb': 78,
    'databoxedge': 44,
    'deploymentmanager': 45,
    'dla': 71,
    'dls': 41,
    'dms': 51,
    'eventgrid': 52,
    'eventhubs': 78,
    # 'extension': 37,
    'feedback': 64,
    'find': 42,
    'hdinsight': 64,
    'identity': 30,
    'interactive': 28,
    'iot': 74,
    'keyvault': 70,
    'kusto': 44,
    'lab': 67,
    'managedservices': 44,
    'maps': 41,
    'marketplaceordering': 29,
    'monitor': 79,
    'natgateway': 46,
    'netappfiles': 65,
    'network': 332,  # series
    'policyinsights': 51,
    'privatedns': 62,
    'profile': 42,
    'rdbms': 80,
    'redis': 53,
    'relay': 71,
    'reservations': 56,
    'resource': 100,
    'role': 49,
    'search': 48,
    'security': 40,
    'servicebus': 52,
    'serviceconnector': 49,
    'servicefabric': 74,
    'signalr': 45,
    'sql': 100,
    'sqlvm': 52,
    'storage': 141,
    'synapse': 68,
    'util': 49,
    'vm': 256,
    'azure-cli-core': 38,
    'azure-cli-testsdk': 75,
    'azure-cli': 25,
    'azure-cli-telemetry': 31,
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


