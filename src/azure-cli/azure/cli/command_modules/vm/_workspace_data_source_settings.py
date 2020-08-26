# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from collections import OrderedDict

linux_performance_collection_properties = [
    {
        'state': 'Enabled'
    }
]

linux_performance_object_properties = [
    {
        "instanceName": "*",
        "intervalSeconds": 10,
        "objectName": "Memory",
        "performanceCounters": [
            {
                "counterName": "Available MBytes Memory"
            },
            {
                "counterName": "% Used Memory"
            },
            {
                "counterName": "% Used Swap Space"
            }
        ]
    },
    {
        "instanceName": "*",
        "intervalSeconds": 10,
        "objectName": "Processor",
        "performanceCounters": [
            {
                "counterName": "% Processor Time"
            },
            {
                "counterName": "% Privileged Time"
            }
        ]
    },
    {
        "instanceName": "*",
        "intervalSeconds": 10,
        "objectName": "Logical Disk",
        "performanceCounters": [
            {
                "counterName": "% Used Inodes"
            },
            {
                "counterName": "Free Megabytes"
            },
            {
                "counterName": "% Used Space"
            },
            {
                "counterName": "Disk Transfers/sec"
            },
            {
                "counterName": "Disk Reads/sec"
            },
            {
                "counterName": "Disk Writes/sec"
            }
        ]
    },
    {
        "instanceName": "*",
        "intervalSeconds": 10,
        "objectName": "Network",
        "performanceCounters": [
            {
                "counterName": "Total Bytes Transmitted"
            },
            {
                "counterName": "Total Bytes Received"
            }
        ]
    }
]

linux_syslog_collection_properties = [
    {
        'state': 'Enabled'
    }
]

linux_syslog_properties = [
    {
        "syslogName": "syslog",
        "syslogSeverities": [
            {
                "severity": "notice"
            },
            {
                "severity": "info"
            },
            {
                "severity": "debug"
            }
        ]
    }
]

windows_event_properties = [
    {
        "eventLogName": "System",
        "eventTypes": [
            {
                "eventType": "Error"
            },
            {
                "eventType": "Warning"
            }
        ]
    }
]

windows_performance_counter_properties = [
    {
        "collectorType": "Default",
        "counterName": "Disk Transfers/sec",
        "instanceName": "*",
        "intervalSeconds": 10,
        "objectName": "LogicalDisk"
    },
    {
        "collectorType": "Default",
        "counterName": "Disk Reads/sec",
        "instanceName": "*",
        "intervalSeconds": 10,
        "objectName": "LogicalDisk"
    },
    {
        "collectorType": "Default",
        "counterName": "Bytes Total/sec",
        "instanceName": "*",
        "intervalSeconds": 10,
        "objectName": "Network Interface"
    },
    {
        "collectorType": "Default",
        "counterName": "Available MBytes",
        "instanceName": "*",
        "intervalSeconds": 10,
        "objectName": "Memory"
    },
    {
        "collectorType": "Default",
        "counterName": "% Free Space",
        "instanceName": "*",
        "intervalSeconds": 10,
        "objectName": "LogicalDisk"
    },
    {
        "collectorType": "Default",
        "counterName": "Avg. Disk sec/Write",
        "instanceName": "*",
        "intervalSeconds": 10,
        "objectName": "LogicalDisk"
    },
    {
        "collectorType": "Default",
        "counterName": "Bytes Received/sec",
        "instanceName": "*",
        "intervalSeconds": 10,
        "objectName": "Network Adapter"
    },
    {
        "collectorType": "Default",
        "counterName": "Current Disk Queue Length",
        "instanceName": "*",
        "intervalSeconds": 10,
        "objectName": "LogicalDisk"
    },
    {
        "collectorType": "Default",
        "counterName": "% Processor Time",
        "instanceName": "_Total",
        "intervalSeconds": 10,
        "objectName": "Processor"
    },
    {
        "collectorType": "Default",
        "counterName": "Free Megabytes",
        "instanceName": "*",
        "intervalSeconds": 10,
        "objectName": "LogicalDisk"
    },
    {
        "collectorType": "Default",
        "counterName": "Avg. Disk sec/Read",
        "instanceName": "*",
        "intervalSeconds": 10,
        "objectName": "LogicalDisk"
    },
    {
        "collectorType": "Default",
        "counterName": "Bytes Sent/sec",
        "instanceName": "*",
        "intervalSeconds": 10,
        "objectName": "Network Adapter"
    },
    {
        "collectorType": "Default",
        "counterName": "% Committed Bytes In Use",
        "instanceName": "*",
        "intervalSeconds": 10,
        "objectName": "Memory"
    },
    {
        "collectorType": "Default",
        "counterName": "Disk Writes/sec",
        "instanceName": "*",
        "intervalSeconds": 10,
        "objectName": "LogicalDisk"
    },
    {
        "collectorType": "Default",
        "counterName": "Processor Queue Length",
        "instanceName": "*",
        "intervalSeconds": 10,
        "objectName": "System"
    }
]

default_linux_data_sources = OrderedDict()

default_linux_data_sources['LinuxPerformanceCollection'] = linux_performance_collection_properties
default_linux_data_sources['LinuxPerformanceObject'] = linux_performance_object_properties
default_linux_data_sources['LinuxSyslogCollection'] = linux_syslog_collection_properties
default_linux_data_sources['LinuxSyslog'] = linux_syslog_properties

default_windows_data_sources = OrderedDict()

default_windows_data_sources['WindowsEvent'] = windows_event_properties
default_windows_data_sources['WindowsPerformanceCounter'] = windows_performance_counter_properties
