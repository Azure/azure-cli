# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from collections import OrderedDict
import re
from subprocess import check_output, STDOUT, CalledProcessError
import sys


TOTAL = 'ALL'
NUM_RUNS = 3
DEFAULT_THRESHOLD = 10
# explicit thresholds that deviate from the default
THRESHOLDS = {
    'network': 30,
    'vm': 30,
    'batch': 30,
    'storage': 50,
    TOTAL: 300
}


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


def print_values(data):
    print('{:<20} {:>12} {:>12} {:>12} {:>25}'.format('Module', 'Average', 'Threshold', 'Stdev', 'Values'))
    for key, val in data.items():
        print('{:<20} {:>12.0f} {:>12.0f} {:>12.0f} {:>25}'.format(
            key, val['average'], val['threshold'], val['stdev'], str(val['values'])))


def run_verifications(args):
    regex = r"[^']*'([^']*)'[\D]*([\d\.]*)"

    results = {TOTAL: []}
    try:
        use_shell = sys.platform.lower() in ['windows', 'win32']
        # Time the module loading X times
        for i in range(0, NUM_RUNS + 1):
            lines = check_output('az -h --debug'.split(), shell=use_shell, stderr=STDOUT)
            if i == 0:
                # Ignore the first run since it can be longer due to *.pyc file compilation
                continue

            try:
                lines = lines.decode().splitlines()
            except:
                lines = lines.splitlines()
            total_time = 0
            for line in lines:
                if line.startswith('DEBUG: Loaded module'):
                    matches = re.match(regex, line)
                    mod = matches.group(1)
                    val = float(matches.group(2)) * 1000
                    total_time = total_time + val
                    if mod in results:
                        results[mod].append(val)
                    else:
                        results[mod] = [val]
            results[TOTAL].append(total_time)

        passed_mods = {}
        failed_mods = {}

        mods = sorted(results.keys())
        bubble_found = False
        for mod in mods:
            val = results[mod]
            mean_val = mean(val)
            stdev_val = pstdev(val)
            threshold = THRESHOLDS.get(mod) or DEFAULT_THRESHOLD
            statistics = {
                'average': mean_val,
                'stdev': stdev_val,
                'threshold': threshold,
                'values': val
            }
            if mean_val > threshold:
                if not bubble_found and mean_val < 30:
                    # This temporary measure allows one floating performance
                    # failure up to 30 ms. See issue #6224 and #6218.
                    bubble_found = True
                    passed_mods[mod] = statistics
                else:
                    failed_mods[mod] = statistics
            else:
                passed_mods[mod] = statistics


        if not failed_mods:
            print('== PASSED MODULES ==')
            print_values(passed_mods)
            print('\nPASSED: Average load time all modules: {} ms'.format(
                int(passed_mods[TOTAL]['average'])))
            sys.exit(0)
        else:
            print('== PASSED MODULES ==')
            print_values(passed_mods)
            print('\nFAILED MODULES')
            print_values(failed_mods)
            sys.exit(1)
    except CalledProcessError as ex:
        print(ex.output)
