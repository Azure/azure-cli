# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import datetime
import json

from azure.cli.core._config import set_global_config_value

from azclishell.configuration import CONFIGURATION, get_config_dir as shell_config

SHELL_CONFIG = CONFIGURATION
DAYS_AGO = 28
ACTIVE_STATUS = 5
DISPLAY_TIME = 20


def update_frequency():
    """ updates the frequency from files """
    try:
        with open(os.path.join(shell_config(), SHELL_CONFIG.get_frequency()), 'r') as freq:
            try:
                frequency = json.load(freq)
            except ValueError:
                frequency = {}
    except IOError:
        open(os.path.join(shell_config(), SHELL_CONFIG.get_frequency()), 'w')
        frequency = {}

    with open(os.path.join(shell_config(), SHELL_CONFIG.get_frequency()), 'w') as freq:
        now = str(datetime.datetime.utcnow())
        val = frequency.get(now)
        frequency[now] = val + 1 if val else 1
        json.dump(frequency, freq)

    return frequency


def frequency_measurement():
    """ measures how many times a user has used this program in the last calendar week """
    freq = update_frequency()
    count = 0
    base = datetime.datetime.utcnow()
    date_list = [base - datetime.timedelta(days=x) for x in range(1, DAYS_AGO)]
    for day in date_list:
        count += 1 if freq.get(day, 0) > 0 else 0
    return count


def frequency_heuristic():
    """ decides whether user meets requirements for frequency """
    return frequency_measurement() >= ACTIVE_STATUS


frequent_user = frequency_heuristic()
