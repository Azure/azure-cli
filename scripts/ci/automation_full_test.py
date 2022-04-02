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
    'acr': 195,
    'acs': 225,
    'advisor': 180,
    'ams': 302,
    'apim': 227,
    'appconfig': 203,
    'appservice': 272,  # series
    'aro': 202,
    'backup': 278,
    'batch': 188,
    'batchai': 189,
    'billing': 182,
    'botservice': 164,  # series
    'cdn': 198,
    'cloud': 159,  # series
    'cognitiveservices': 203,
    'config': 186,
    'configure': 180,
    'consumption': 183,
    'container': 185,
    'cosmosdb': 218,
    'databoxedge': 184,
    'deploymentmanager': 185,
    'dla': 211,
    'dls': 181,
    'dms': 191,
    'eventgrid': 192,
    'eventhubs': 218,
    # 'extension': 177,
    'feedback': 204,
    'find': 182,
    'hdinsight': 204,
    'identity': 170,
    'interactive': 168,
    'iot': 214,
    'keyvault': 210,
    'kusto': 184,
    'lab': 207,
    'managedservices': 184,
    'maps': 181,
    'marketplaceordering': 169,
    'monitor': 219,
    'natgateway': 186,
    'netappfiles': 205,
    'network': 472,  # series
    'policyinsights': 191,
    'privatedns': 202,
    'profile': 182,
    'rdbms': 220,
    'redis': 193,
    'relay': 211,
    'reservations': 196,
    'resource': 240,
    'role': 189,
    'search': 188,
    'security': 180,
    'servicebus': 192,
    'serviceconnector': 189,
    'servicefabric': 214,
    'signalr': 185,
    'sql': 240,
    'sqlvm': 192,
    'storage': 281,
    'synapse': 208,
    'util': 189,
    'vm': 396,
    'azure-cli-core': 178,
    'azure-cli-testsdk': 215,
    'azure-cli': 165,
    'azure-cli-telemetry': 171,
 }

series_modules = ['appservice', 'botservice', 'cloud', 'network']
part, part_idx = [int(i) for i in sys.argv[1].split('_')]
parallel, para_idx = [int(i) for i in sys.argv[2].split('_')]
profile = sys.argv[3]

jobs = sorted(jobs.items(), key=lambda item:-item[1])
# pprint(jobs)
# pprint(len(jobs))

parallel = 8
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
    # part, part_idx = [int(i) for i in '4_1'.split('_')]
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


