# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function

from collections import OrderedDict
import re
from subprocess import check_output, STDOUT, CalledProcessError
import sys


NUM_RUNS = 3

HIGH_THRESHOLD = 35
HIGH_MODULES = ['network', 'vm', 'batch', 'storage']
LO_THRESHOLD = 10


def init(root):
    parser = root.add_parser('module-load-perf', help='Verify that modules load within an acceptable timeframe.')
    parser.set_defaults(func=run_verifications)


def mean(data):
    """Return the sample arithmetic mean of data."""
    n = len(data)
    if n < 1:
        raise ValueError('len < 1')
    return sum(data)/float(n)


def sq_deviation(data):
    """Return sum of square deviations of sequence data."""
    c = mean(data)
    return sum((x-c)**2 for x in data)


def pstdev(data):
    """Calculates the population standard deviation."""
    n = len(data)
    if n < 2:
        raise ValueError('len < 2')
    ss = sq_deviation(data)
    return (ss/n) ** 0.5

def run_verifications(args):
    regex = r"[^']*'([^']*)'[\D]*([\d\.]*)"

    results = {}
    try:
        # Time the module loading X times
        for _ in range(0, NUM_RUNS):
            use_shell = sys.platform.lower() in ['windows', 'win32']
            lines = check_output('az -h --debug'.split(), shell=use_shell, stderr=STDOUT)
            try:
                lines = lines.decode().splitlines()
            except:
                lines = lines.splitlines()
            for line in lines:
                if line.startswith('DEBUG: Loaded module'):
                    matches = re.match(regex, line)
                    mod = matches.group(1)
                    val = float(matches.group(2)) * 1000
                    if mod in results:
                        results[mod].append(val)
                    else:
                        results[mod] = [val]

        failed_mods = []
        print('{:<20} {:>12} {:>12}'.format('Module', 'Average', 'Stdev'))
        mods = sorted(results.keys())
        for mod in mods:
            val = results[mod]
            mean_val = mean(val)
            stdev_val = pstdev(val)
            print('{:<20} {:>12.0f} {:>12.0f}'.format(mod, mean_val, stdev_val))
            threshold = HIGH_THRESHOLD if mod in HIGH_MODULES else LO_THRESHOLD
            if mean_val > threshold:
                failed_mods.append({
                    'name': mod,
                    'average': mean_val,
                    'stdev': stdev_val,
                    'threshold': threshold
                })


        if failed_mods:
            print('\nFAILED MODULES')
            print('{:<20} {:>12} {:>12}'.format('Module', 'Average', 'Threshold'))
            for item in failed_mods:
                print('{:<20} {:>12.0f} {:>12.0f}'.format(item['name'], item['average'], item['threshold']))
    except CalledProcessError as ex:
        print(ex.output)
