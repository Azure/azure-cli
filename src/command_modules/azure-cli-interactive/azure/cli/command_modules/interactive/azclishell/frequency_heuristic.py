# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import datetime
import json

DAYS_AGO = 28
ACTIVE_STATUS = 5
DISPLAY_TIME = 20


def day_format(now):
    """ returns the date format """
    return now.strftime("%Y-%m-%d")


def update_frequency(shell_ctx):
    """ updates the frequency from files """
    frequency_path = os.path.join(shell_ctx.config.get_config_dir(), shell_ctx.config.get_frequency())
    if os.path.exists(frequency_path):
        with open(frequency_path, 'r') as freq:
            try:
                frequency = json.load(freq)
            except ValueError:
                frequency = {}
    else:
        frequency = {}

    with open(frequency_path, 'w') as freq:
        now = day_format(datetime.datetime.utcnow())
        val = frequency.get(now)
        frequency[now] = val + 1 if val else 1
        json.dump(frequency, freq)

    return frequency


def frequency_measurement(shell_ctx):
    """ measures how many times a user has used this program in the last calendar week """
    freq = update_frequency(shell_ctx)
    count = 0
    base = datetime.datetime.utcnow()
    date_list = [base - datetime.timedelta(days=x) for x in range(0, DAYS_AGO)]
    for day in date_list:
        count += 1 if freq.get(day_format(day), 0) > 0 else 0

    return count


def frequency_heuristic(shell_ctx):
    """ decides whether user meets requirements for frequency """
    return frequency_measurement(shell_ctx) >= ACTIVE_STATUS
