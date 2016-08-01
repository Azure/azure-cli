#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

import json
import os
from azure.cli._util import get_file_json

def read_content_if_is_file(string_or_file):
    content = string_or_file
    if os.path.exists(string_or_file):
        with open(string_or_file, 'r') as f:
            content = f.read()
    return content

def load_json(string_or_file_path):
    if os.path.exists(string_or_file_path):
        return get_file_json(string_or_file_path)
    else:
        return json.loads(string_or_file_path)

def get_default_linux_diag_config(vm_id=None):
    #pylint: disable=bad-continuation
    return {
      'diagnosticMonitorConfiguration': {
        'metrics': {
          'resourceId': vm_id or 'resource id of the virtual machine',
          'metricAggregation': [{
              'scheduledTransferPeriod': 'PT1H'
            },
            {
              'scheduledTransferPeriod': 'PT1M'
            }]
        },
        'performanceCounters': {
          'performanceCounterConfiguration': [{
              'class': 'Memory',
              'counterSpecifier': 'PercentAvailableMemory',
              'table': 'LinuxMemory'
            }, {
              'class': 'Memory',
              'counterSpecifier': 'AvailableMemory',
              'table': 'LinuxMemory'
            }, {
              'class': 'Memory',
              'counterSpecifier': 'UsedMemory',
              'table': 'LinuxMemory'
            }, {
              'class': 'Memory',
              'counterSpecifier': 'PercentUsedSwap',
              'table': 'LinuxMemory'
            }, {
              'class': 'Processor',
              'counterSpecifier': 'PercentProcessorTime',
              'table': 'LinuxCpu'
            }, {
              'class': 'Processor',
              'counterSpecifier': 'PercentIOWaitTime',
              'table': 'LinuxCpu'
            }, {
              'class': 'Processor',
              'counterSpecifier': 'PercentIdleTime',
              'table': 'LinuxCpu'
            }, {
              'class': 'PhysicalDisk',
              'counterSpecifier': 'AverageWriteTime',
              'table': 'LinuxDisk'
            }, {
              'class': 'PhysicalDisk',
              'counterSpecifier': 'AverageReadTime',
              'table': 'LinuxDisk'
            }, {
              'class': 'PhysicalDisk',
              'counterSpecifier': 'ReadBytesPerSecond',
              'table': 'LinuxDisk'
            }, {
              'class': 'PhysicalDisk',
              'counterSpecifier': 'WriteBytesPerSecond',
              'table': 'LinuxDisk'
            }]
        }
      }
    }
