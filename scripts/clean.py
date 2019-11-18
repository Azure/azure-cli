# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# Azure Killer
# version 0.1
# Clean Azure resources automatically

import os
import json
import datetime

# Please set parameters

# Subscription ID
subscription = '0b1f6471-1bf0-4dda-aec3-cb9272f09590'

# Prefix of resource group that will not be deleted
prefixes = []

# Maximum survival time, in days
TTL = 3


def main():
    print('Azure Killer, version 0.1')
    print('Configuration:')
    print('    Subscription: ' + subscription)
    print('    Resource group prefix: ' + str(prefixes))
    print('    Maximum survival time: %d days' % TTL)
    print()
    cmd = 'az group list --subscription %s --query [].name'
    result = os.popen(cmd % subscription).read()
    rgs = json.loads(result)
    for rg in rgs:
        clean_rg(rg)


def clean_rg(rg):
    """
    Clean resource group.
    :param rg: Resource group name
    :return:
    """
    print('Processing resource group: ' + rg)
    cmd = 'az monitor activity-log list --offset 10d --max-events 99999999 --query [].eventTimestamp -g %s'
    result = os.popen(cmd % rg).read()
    dates = json.loads(result)
    if old_enough(dates) and target_rg(rg):
        cmd = 'az group delete -y -g %s --subscription %s' % (rg, subscription)
        print(cmd)
        os.popen(cmd)


def old_enough(dates):
    """
    Whether it's old enough.
    :param dates: Array of dates
    :return: bool
    """
    if not dates:
        print('Duration: too old')
        return True
    date = dates[-1]
    date = datetime.datetime.strptime(date, '%Y-%m-%dT%H:%M:%S.%f+00:00')
    now = datetime.datetime.utcnow()
    duration = now - date
    print('Duration: ' + str(duration))
    return duration.days > TTL


def target_rg(rg):
    """
    Whether should delete the rg.
    :param rg: Resource group name
    :return: bool
    """
    return not any(rg.startswith(prefix) for prefix in prefixes)


if __name__ == '__main__':
    main()
