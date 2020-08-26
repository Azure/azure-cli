# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def set_metrics(client, retention, hour=None, minute=None, api=None, timeout=None):
    for s in client:
        s.set_metrics(retention, hour, minute, api, timeout)


def get_metrics(client, interval='both', timeout=None):
    results = {}
    for s in client:
        results[s.name] = s.get_metrics(interval, timeout)
    return results
