# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

import re

from knack.log import get_logger
from knack.util import CLIError

from azdev.utilities import (
    display, heading, subheading, cmd, require_azure_cli)

logger = get_logger(__name__)

TOTAL = 'ALL'
TOTAL_THRESHOLD = 300
DEFAULT_THRESHOLD = 10
THRESHOLDS = {
    # threshold value: num of exceptions allowed
    50: 2,
    40: 3
}


# pylint: disable=too-many-statements
def check_load_time(runs=3):

    require_azure_cli()

    heading('Module Load Performance')

    regex = r"[^']*'(?P<mod>[^']*)'[\D]*(?P<val>[\d\.]*)"

    results = {TOTAL: []}
    # Time the module loading X times
    for i in range(0, runs + 1):
        lines = cmd('az -h --debug', show_stderr=True).result
        if i == 0:
            # Ignore the first run since it can be longer due to *.pyc file compilation
            continue

        try:
            lines = lines.decode().splitlines()
        except AttributeError:
            lines = lines.splitlines()
        total_time = 0
        for line in lines:
            if line.startswith('DEBUG: Loaded module'):
                matches = re.match(regex, line)
                mod = matches.group('mod')
                val = float(matches.group('val')) * 1000
                total_time = total_time + val
                if mod in results:
                    results[mod].append(val)
                else:
                    results[mod] = [val]
        results[TOTAL].append(total_time)

    passed_mods = {}
    failed_mods = {}

    def _claim_higher_threshold(val):
        avail_thresholds = {k: v for k, v in THRESHOLDS.items() if v}
        new_threshold = None
        for threshold in sorted(avail_thresholds):
            if val < threshold:
                THRESHOLDS[threshold] = THRESHOLDS[threshold] - 1
                new_threshold = threshold
            break
        return new_threshold

    mods = sorted(results.keys())
    for mod in mods:
        val = results[mod]
        mean_val = mean(val)
        stdev_val = pstdev(val)
        threshold = TOTAL_THRESHOLD if mod == TOTAL else DEFAULT_THRESHOLD
        statistics = {
            'average': mean_val,
            'stdev': stdev_val,
            'threshold': threshold,
            'values': val
        }
        if mean_val > threshold:
            # claim a threshold exception if available
            new_threshold = _claim_higher_threshold(mean_val)
            if new_threshold:
                statistics['threshold'] = new_threshold
                passed_mods[mod] = statistics
            else:
                failed_mods[mod] = statistics
        else:
            passed_mods[mod] = statistics

    subheading('Results')
    if failed_mods:
        display('== PASSED MODULES ==')
        display_table(passed_mods)
        display('\nFAILED MODULES')
        display_table(failed_mods)
        raise CLIError("""
FAILED: Some modules failed. If values are close to the threshold, rerun. If values
are large, check that you do not have top-level imports like azure.mgmt or msrestazure
in any modified files.
""")

    display('== PASSED MODULES ==')
    display_table(passed_mods)
    display('\nPASSED: Average load time all modules: {} ms'.format(
        int(passed_mods[TOTAL]['average'])))


def mean(data):
    """Return the sample arithmetic mean of data."""
    n = len(data)
    if n < 1:
        raise ValueError('len < 1')
    return sum(data) / float(n)


def sq_deviation(data):
    """Return sum of square deviations of sequence data."""
    c = mean(data)
    return sum((x - c) ** 2 for x in data)


def pstdev(data):
    """Calculates the population standard deviation."""
    n = len(data)
    if n < 2:
        raise ValueError('len < 2')
    ss = sq_deviation(data)
    return (ss / n) ** 0.5


def display_table(data):
    display('{:<20} {:>12} {:>12} {:>12} {:>25}'.format('Module', 'Average', 'Threshold', 'Stdev', 'Values'))
    for key, val in data.items():
        display('{:<20} {:>12.0f} {:>12.0f} {:>12.0f} {:>25}'.format(
            key, val['average'], val['threshold'], val['stdev'], str(val['values'])))
