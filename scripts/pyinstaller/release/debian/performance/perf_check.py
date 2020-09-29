# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import sys
import time
import platform
from subprocess import check_output

BENCHMARK_COMMANDS = [
    'az version',
    'az -h',
    'az vm -h',
    'az vm create -h',
    'az network -h',
]


def parse_real_cost(output):
    cost = None
    for line in output.splitlines():
        if 'real' in line:
            start_index = line.index('0m') + 2
            end_index = line.index('s', start_index)
            cost_str = line[start_index:end_index]
            cost = float(cost_str)
            break
    return cost


class CommandCost(object):
    def __init__(self, command):
        self.command = command
        self.released_command = 'time {}'.format(command).split()
        self.pyinstaller_command = 'time /opt/paz/{}'.format(command).split()
        self.costs = []

    def run(self):
        released_output = check_output(self.released_command, shell=platform.system() == 'Windows')
        released_cost = parse_real_cost(released_output)

        pyinstaller_output = check_output(self.pyinstaller_command, shell=platform.system() == 'Windows')
        pyinstaller_cost = parse_real_cost(pyinstaller_output)
        self.costs.append((released_cost, pyinstaller_cost))
    
    def avg(self):
        released_cost, pyinstaller_cost = 0, 0
        for cost in self.costs:
            released_cost += cost[0]
            pyinstaller_cost += cost[1]
        return (released_cost / len(self.costs), pyinstaller_cost / len(self.costs))
    
    def __str__(self):
        s = '--------------------{}--------------------\n'.format(command_cost.command)
        for cost in self.costs:
            s += 'current release: {}, pyinstaller: {}\n'.format(cost[0], cost[1])
        s += 'Avg:\n'
        release_avg, pyinstaller_avg = self.avg()
        s += 'current release: {}, pyinstaller: {}\n'.format(release_avg, pyinstaller_avg)
        return s


if __name__ == '__main__':
    command_costs = [CommandCost(c) for c in BENCHMARK_COMMANDS]

    TEST_COUNT = 20
    while TEST_COUNT > 0:
        for command_cost in command_costs:
            command_cost.run()
        time.sleep(10)
        TEST_COUNT -= 1

    for command_cost in command_costs:
        print(str(command_cost))

    exist_code = 0
    for command_cost in command_costs:
        release_avg, pyinstaller_avg = command_cost.avg()
        if pyinstaller_avg > release_avg * 1.2:
            exist_code = 1
            break
    sys.exit(exist_code)
