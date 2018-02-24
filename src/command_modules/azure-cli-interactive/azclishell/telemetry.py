# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import azure.cli.core.telemetry as telemetry_core


class Telemetry(object):
    """ Handles Interactive Telemetry """

    def __init__(self):
        self.core = telemetry_core


_session = Telemetry()


# core telemetry operations
def start():
    telemetry_core.start()

def flush():
    telemetry_core.flush()

def conclude():
    telemetry_core.conclude()

def set_failure(summary=None):
    telemetry_core.set_failure(summary=summary)

def set_success(summary=None):
    telemetry_core.set_success(summary=summary)


# # operations for aggregating data
# def 