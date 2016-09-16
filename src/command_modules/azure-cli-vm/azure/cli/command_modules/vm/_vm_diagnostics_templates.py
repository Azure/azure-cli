#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------
#pylint: skip-file
def get_default_diag_config(is_windows):
    if is_windows:
        return             {
              "WadCfg": {
                "DiagnosticMonitorConfiguration": {
                  "overallQuotaInMB": "4096",
                  "DiagnosticInfrastructureLogs": {
                    "scheduledTransferLogLevelFilter": "Error"
                  },
                  "WindowsEventLog": {
                    "scheduledTransferPeriod": "PT1M",
                    "DataSource": [
                      { "name": "Application!*[System[(Level = 1) or (Level = 2)]]" },
                      { "name": "Security!*[System[(Level = 1 or Level = 2)]]" },
                      { "name": "System!*[System[(Level = 1 or Level = 2)]]" }
                    ]
                  },
                  "PerformanceCounters": {
                    "scheduledTransferPeriod": "PT1M",
                    "PerformanceCounterConfiguration": [
                      {
                        "counterSpecifier": "\\Processor(_Total)\\% Processor Time",
                        "sampleRate": "PT15S",
                        "unit": "Percent",
                        "annotation": [
                          {
                            "displayName": "CPU utilization",
                            "locale": "en-us"
                          }
                        ]
                      },
                      {
                        "counterSpecifier": "\\Processor(_Total)\\% Privileged Time",
                        "sampleRate": "PT15S",
                        "unit": "Percent",
                        "annotation": [
                          {
                            "displayName": "CPU privileged time",
                            "locale": "en-us"
                          }
                        ]
                      },
                      {
                        "counterSpecifier": "\\Processor(_Total)\\% User Time",
                        "sampleRate": "PT15S",
                        "unit": "Percent",
                        "annotation": [
                          {
                            "displayName": "CPU user time",
                            "locale": "en-us"
                          }
                        ]
                      },
                      {
                        "counterSpecifier": "\\Processor Information(_Total)\\Processor Frequency",
                        "sampleRate": "PT15S",
                        "unit": "Count",
                        "annotation": [
                          {
                            "displayName": "CPU frequency",
                            "locale": "en-us"
                          }
                        ]
                      },
                      {
                        "counterSpecifier": "\\System\\Processes",
                        "sampleRate": "PT15S",
                        "unit": "Count",
                        "annotation": [
                          {
                            "displayName": "Processes",
                            "locale": "en-us"
                          }
                        ]
                      },
                      {
                        "counterSpecifier": "\\Process(_Total)\\Thread Count",
                        "sampleRate": "PT15S",
                        "unit": "Count",
                        "annotation": [
                          {
                            "displayName": "Threads",
                            "locale": "en-us"
                          }
                        ]
                      },
                      {
                        "counterSpecifier": "\\Process(_Total)\\Handle Count",
                        "sampleRate": "PT15S",
                        "unit": "Count",
                        "annotation": [
                          {
                            "displayName": "Handles",
                            "locale": "en-us"
                          }
                        ]
                      },
                      {
                        "counterSpecifier": "\\Memory\\% Committed Bytes In Use",
                        "sampleRate": "PT15S",
                        "unit": "Percent",
                        "annotation": [
                          {
                            "displayName": "Memory usage",
                            "locale": "en-us"
                          }
                        ]
                      },
                      {
                        "counterSpecifier": "\\Memory\\Available Bytes",
                        "sampleRate": "PT15S",
                        "unit": "Bytes",
                        "annotation": [
                          {
                            "displayName": "Memory available",
                            "locale": "en-us"
                          }
                        ]
                      },
                      {
                        "counterSpecifier": "\\Memory\\Committed Bytes",
                        "sampleRate": "PT15S",
                        "unit": "Bytes",
                        "annotation": [
                          {
                            "displayName": "Memory committed",
                            "locale": "en-us"
                          }
                        ]
                      },
                      {
                        "counterSpecifier": "\\Memory\\Commit Limit",
                        "sampleRate": "PT15S",
                        "unit": "Bytes",
                        "annotation": [
                          {
                            "displayName": "Memory commit limit",
                            "locale": "en-us"
                          }
                        ]
                      },
                      {
                        "counterSpecifier": "\\PhysicalDisk(_Total)\\% Disk Time",
                        "sampleRate": "PT15S",
                        "unit": "Percent",
                        "annotation": [
                          {
                            "displayName": "Disk active time",
                            "locale": "en-us"
                          }
                        ]
                      },
                      {
                        "counterSpecifier": "\\PhysicalDisk(_Total)\\% Disk Read Time",
                        "sampleRate": "PT15S",
                        "unit": "Percent",
                        "annotation": [
                          {
                            "displayName": "Disk active read time",
                            "locale": "en-us"
                          }
                        ]
                      },
                      {
                        "counterSpecifier": "\\PhysicalDisk(_Total)\\% Disk Write Time",
                        "sampleRate": "PT15S",
                        "unit": "Percent",
                        "annotation": [
                          {
                            "displayName": "Disk active write time",
                            "locale": "en-us"
                          }
                        ]
                      },
                      {
                        "counterSpecifier": "\\PhysicalDisk(_Total)\\Disk Transfers/sec",
                        "sampleRate": "PT15S",
                        "unit": "CountPerSecond",
                        "annotation": [
                          {
                            "displayName": "Disk operations",
                            "locale": "en-us"
                          }
                        ]
                      },
                      {
                        "counterSpecifier": "\\PhysicalDisk(_Total)\\Disk Reads/sec",
                        "sampleRate": "PT15S",
                        "unit": "CountPerSecond",
                        "annotation": [
                          {
                            "displayName": "Disk read operations",
                            "locale": "en-us"
                          }
                        ]
                      },
                      {
                        "counterSpecifier": "\\PhysicalDisk(_Total)\\Disk Writes/sec",
                        "sampleRate": "PT15S",
                        "unit": "CountPerSecond",
                        "annotation": [
                          {
                            "displayName": "Disk write operations",
                            "locale": "en-us"
                          }
                        ]
                      },
                      {
                        "counterSpecifier": "\\PhysicalDisk(_Total)\\Disk Bytes/sec",
                        "sampleRate": "PT15S",
                        "unit": "BytesPerSecond",
                        "annotation": [
                          {
                            "displayName": "Disk speed",
                            "locale": "en-us"
                          }
                        ]
                      },
                      {
                        "counterSpecifier": "\\PhysicalDisk(_Total)\\Disk Read Bytes/sec",
                        "sampleRate": "PT15S",
                        "unit": "BytesPerSecond",
                        "annotation": [
                          {
                            "displayName": "Disk read speed",
                            "locale": "en-us"
                          }
                        ]
                      },
                      {
                        "counterSpecifier": "\\PhysicalDisk(_Total)\\Disk Write Bytes/sec",
                        "sampleRate": "PT15S",
                        "unit": "BytesPerSecond",
                        "annotation": [
                          {
                            "displayName": "Disk write speed",
                            "locale": "en-us"
                          }
                        ]
                      },
                      {
                        "counterSpecifier": "\\LogicalDisk(_Total)\\% Free Space",
                        "sampleRate": "PT15S",
                        "unit": "Percent",
                        "annotation": [
                          {
                            "displayName": "Disk free space (percentage)",
                            "locale": "en-us"
                          }
                        ]
                      }
                    ]
                  },
                  "Metrics": {
                    "resourceId": "[variables('wadmetricsresourceid')]",
                    "MetricAggregation": [
                      {
                        "scheduledTransferPeriod": "PT1H"
                      },
                      {
                        "scheduledTransferPeriod": "PT1M"
                      }
                    ]
                  }
                }
              },
              "storageAccount": "<name of a storage account>"
            }
    else:
        return {
              "ladCfg": {
                "diagnosticMonitorConfiguration": {
                  "performanceCounters": {
                    "performanceCounterConfiguration": [
                      { 
                        "namespace": "root/scx",
                        "class": "Memory",
                        "counterSpecifier": "AvailableMemory",
                        "table": "LinuxMemory"
                      },
                      { 
                        "namespace": "root/scx",
                        "class": "Memory",
                        "counterSpecifier": "PercentAvailableMemory",
                        "table": "LinuxMemory"
                      },
                      { 
                        "namespace": "root/scx",
                        "class": "Memory",
                        "counterSpecifier": "UsedMemory",
                        "table": "LinuxMemory"
                      },
                      { 
                        "namespace": "root/scx",
                        "class": "Memory",
                        "counterSpecifier": "PercentUsedMemory",
                        "table": "LinuxMemory"
                      },
                      { 
                        "namespace": "root/scx",
                        "class": "Memory",
                        "counterSpecifier": "PercentUsedByCache",
                        "table": "LinuxMemory"
                      },
                      { 
                        "namespace": "root/scx",
                        "class": "Memory",
                        "counterSpecifier": "PagesPerSec",
                        "table": "LinuxMemory"
                      },
                      { 
                        "namespace": "root/scx",
                        "class": "Memory",
                        "counterSpecifier": "PagesReadPerSec",
                        "table": "LinuxMemory"
                      },
                      { 
                        "namespace": "root/scx",
                        "class": "Memory",
                        "counterSpecifier": "PagesWrittenPerSec",
                        "table": "LinuxMemory"
                      },
                      { 
                        "namespace": "root/scx",
                        "class": "Memory",
                        "counterSpecifier": "AvailableSwap",
                        "table": "LinuxMemory"
                      },
                      { 
                        "namespace": "root/scx",
                        "class": "Memory",
                        "counterSpecifier": "PercentAvailableSwap",
                        "table": "LinuxMemory"
                      },
                      { 
                        "namespace": "root/scx",
                        "class": "Memory",
                        "counterSpecifier": "UsedSwap",
                        "table": "LinuxMemory"
                      },
                      { 
                        "namespace": "root/scx",
                        "class": "Memory",
                        "counterSpecifier": "PercentUsedSwap",
                        "table": "LinuxMemory"
                      },
                      { 
                        "namespace": "root/scx",
                        "class": "Processor",
                        "counterSpecifier": "PercentIdleTime",
                        "table": "LinuxProcessor"
                      },
                      { 
                        "namespace": "root/scx",
                        "class": "Processor",
                        "counterSpecifier": "PercentUserTime",
                        "table": "LinuxProcessor"
                      },
                      { 
                        "namespace": "root/scx",
                        "class": "Processor",
                        "counterSpecifier": "PercentNiceTime",
                        "table": "LinuxProcessor"
                      },
                      { 
                        "namespace": "root/scx",
                        "class": "Processor",
                        "counterSpecifier": "PercentPrivilegedTime",
                        "table": "LinuxProcessor"
                      },
                      { 
                        "namespace": "root/scx",
                        "class": "Processor",
                        "counterSpecifier": "PercentInterruptTime",
                        "table": "LinuxProcessor"
                      },
                      { 
                        "namespace": "root/scx",
                        "class": "Processor",
                        "counterSpecifier": "PercentDPCTime",
                        "table": "LinuxProcessor"
                      },
                      { 
                        "namespace": "root/scx",
                        "class": "Processor",
                        "counterSpecifier": "PercentProcessorTime",
                        "table": "LinuxProcessor"
                      },
                      { 
                        "namespace": "root/scx",
                        "class": "Processor",
                        "counterSpecifier": "PercentIOWaitTime",
                        "table": "LinuxProcessor"
                      },
                      { 
                        "namespace": "root/scx",
                        "class": "PhysicalDisk",
                        "counterSpecifier": "BytesPerSecond",
                        "table": "LinuxPhysicalDisk"
                      },
                      { 
                        "namespace": "root/scx",
                        "class": "PhysicalDisk",
                        "counterSpecifier": "ReadBytesPerSecond",
                        "table": "LinuxPhysicalDisk"
                      },
                      { 
                        "namespace": "root/scx",
                        "class": "PhysicalDisk",
                        "counterSpecifier": "WriteBytesPerSecond",
                        "table": "LinuxPhysicalDisk"
                      },
                      { 
                        "namespace": "root/scx",
                        "class": "PhysicalDisk",
                        "counterSpecifier": "TransfersPerSecond",
                        "table": "LinuxPhysicalDisk"
                      },
                      { 
                        "namespace": "root/scx",
                        "class": "PhysicalDisk",
                        "counterSpecifier": "ReadsPerSecond",
                        "table": "LinuxPhysicalDisk"
                      },
                      { 
                        "namespace": "root/scx",
                        "class": "PhysicalDisk",
                        "counterSpecifier": "WritesPerSecond",
                        "table": "LinuxPhysicalDisk"
                      },
                      { 
                        "namespace": "root/scx",
                        "class": "PhysicalDisk",
                        "counterSpecifier": "AverageReadTime",
                        "table": "LinuxPhysicalDisk"
                      },
                      { 
                        "namespace": "root/scx",
                        "class": "PhysicalDisk",
                        "counterSpecifier": "AverageWriteTime",
                        "table": "LinuxPhysicalDisk"
                      },
                      { 
                        "namespace": "root/scx",
                        "class": "PhysicalDisk",
                        "counterSpecifier": "AverageTransferTime",
                        "table": "LinuxPhysicalDisk"
                      },
                      { 
                        "namespace": "root/scx",
                        "class": "PhysicalDisk",
                        "counterSpecifier": "AverageDiskQueueLength",
                        "table": "LinuxPhysicalDisk"
                      },
                      { 
                        "namespace": "root/scx",
                        "class": "NetworkInterface",
                        "counterSpecifier": "BytesTransmitted",
                        "table": "LinuxNetworkInterface"
                      },
                      { 
                        "namespace": "root/scx",
                        "class": "NetworkInterface",
                        "counterSpecifier": "BytesReceived",
                        "table": "LinuxNetworkInterface"
                      },
                      { 
                        "namespace": "root/scx",
                        "class": "NetworkInterface",
                        "counterSpecifier": "PacketsTransmitted",
                        "table": "LinuxNetworkInterface"
                      },
                      { 
                        "namespace": "root/scx",
                        "class": "NetworkInterface",
                        "counterSpecifier": "PacketsReceived",
                        "table": "LinuxNetworkInterface"
                      },
                      { 
                        "namespace": "root/scx",
                        "class": "NetworkInterface",
                        "counterSpecifier": "BytesTotal",
                        "table": "LinuxNetworkInterface"
                      },
                      { 
                        "namespace": "root/scx",
                        "class": "NetworkInterface",
                        "counterSpecifier": "TotalRxErrors",
                        "table": "LinuxNetworkInterface"
                      },
                      { 
                        "namespace": "root/scx",
                        "class": "NetworkInterface",
                        "counterSpecifier": "TotalTxErrors",
                        "table": "LinuxNetworkInterface"
                      },
                      { 
                        "namespace": "root/scx",
                        "class": "NetworkInterface",
                        "counterSpecifier": "TotalCollisions",
                        "table": "LinuxNetworkInterface"
                      }
                    ]
                  },
                  "metrics": {
                    "resourceId": "[variables('ladMetricsResourceId')]",
                    "metricAggregation": [{
                      "scheduledTransferPeriod": "PT1H"
                    }, {
                      "scheduledTransferPeriod": "PT1M"
                    }]
                  }
                }
              },
              "storageAccount": "<name of a storage account>"
            }
            