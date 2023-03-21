# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# Azure Killer
# version 0.1
# Clean Azure resources automatically
import datetime
import json
import os
import subprocess

# Please set parameters

# Subscription ID
subscription = '0b1f6471-1bf0-4dda-aec3-cb9272f09590'

# Prefix of resource group that will be deleted
prefixes = ['cli_test', 'clitest']

# Maximum survival time, in days
TTL = 1


def main():
    print('Azure Killer, version 0.1')
    print('Configuration:')
    print('    Subscription: ' + subscription)
    print('    Resource group prefix: ' + str(prefixes))
    # print('    Maximum survival time: %d days' % TTL)
    print()
    cmd = 'az group list --subscription %s --query [].name'
    result = os.popen(cmd % subscription).read()
    rgs = json.loads(result)
    for rg in rgs:
        if target_rg(rg):
            clean_rg(rg)


def clean_rg(rg):
    """
    Clean resource group.
    :param rg: Resource group name
    :return:
    """
    print('Processing resource group: ' + rg)
    cmd = ["az", "group", "delete", "-y", "-g", rg, "--subscription", subscription]
    print(cmd)
    try:
        subprocess.run(cmd, timeout=300)
    except subprocess.TimeoutExpired:
        print("Exec command %s timed out" % cmd)
    except Exception as e:
        print("Exec command %s failed" % cmd)
        print(e)


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
    Whether rg has certain prefix.
    :param rg: Resource group name
    :return: bool
    """
    return any(rg.startswith(prefix) for prefix in prefixes)


if __name__ == '__main__':
    main()
