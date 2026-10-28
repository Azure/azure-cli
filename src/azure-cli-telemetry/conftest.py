# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Keep pytest-forked working with pytest 9.2+.

`azdev test` runs pytest with --forked. pytest 9.2 stores a NodeId object in a report's
private ``_id`` field, which pytest-forked 1.7.5 cannot marshal, so every forked test
exits with status 3. Replace that field with the public string ``nodeid`` accepted by
TestReport. Reports from older pytest versions are left unchanged.
"""

from functools import wraps


def pytest_configure(config):
    forked = config.pluginmanager.getplugin("pytest_forked")
    if forked is None:
        return

    original = forked.serialize_report

    @wraps(original)
    def serialize_report(report):
        data = original(report)
        if "_id" in data:
            del data["_id"]
            data["nodeid"] = report.nodeid
        return data

    forked.serialize_report = serialize_report
    config.add_cleanup(lambda: setattr(forked, "serialize_report", original))
