# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def set_logging(client, log, retention, timeout=None):
    for s in client:
        s.set_logging('r' in log, 'w' in log, 'd' in log, retention, timeout)


def get_logging(client, timeout=None):
    results = {}
    for s in client:
        results[s.name] = s.get_logging(timeout)
    return results
