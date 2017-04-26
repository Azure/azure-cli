# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import datetime
import json

from azclishell.configuration import CONFIGURATION, get_config_dir

SHELL_CONFIG = CONFIGURATION
DAYS_AGO = 28
ACTIVE_STATUS = 5

def today_format(now):
    """ returns the date format """
    return now.strftime("%Y-%m-%d")


def update_frequency():
    """ updates the frequency from files """
    with open(os.path.join(get_config_dir(), SHELL_CONFIG.get_frequency()), 'r') as freq:
        try:
            frequency = json.load(freq)
        except ValueError:
            frequency = {}

    with open(os.path.join(get_config_dir(), SHELL_CONFIG.get_frequency()), 'w') as freq:
        now = datetime.datetime.now()
        now = today_format(now)
        val = frequency.get(now)
        frequency[now] = val + 1 if val else 1
        json.dump(frequency, freq)

    return frequency


def frequency_measurement():
    """ measures how many times a user has used this program in the last calendar week """
    freq = update_frequency()
    count = 0
    base = datetime.datetime.now()
    date_list = [base - datetime.timedelta(days=x) for x in range(1, DAYS_AGO)]
    for day in date_list:
        count += 1 if freq.get(today_format(day), 0) > 0 else 0
    return count


def frequency_heuristic():
    """ decides whether user meets requirements for frequency """
    return frequency_measurement() >= ACTIVE_STATUS


frequent_user = frequency_heuristic()