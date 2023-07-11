# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: skip-file

data_source_name = "DataSource_CustomLog_SQLAssessment_CL"
dcr_source_pattern = "C:\\Windows\\System32\\config\\systemprofile\\AppData\\Local\\Microsoft SQL Server IaaS Agent\\Assessment\\*.csv"
custom_log_name = "Custom-SqlAssessment_CL"
table_name = "SqlAssessment_CL"

# KEEP BELOW. LEGACY CODE. Keep for possible revert based on Custom Table deprecation.
data_source_kind = "CustomLog"

data_source_properties = {
    "customLogName": "SqlAssessment",
    "description": "The Sql Assessment results",
    "extractions": [
        {
            "extractionName": "TimeGenerated",
            "extractionProperties": {
                "dateTimeExtraction": {
                    "regex": [
                        {
                            "matchIndex": 0,
                            "pattern": "((\\d{2})|(\\d{4}))-([0-1]\\d)-(([0-3]\\d)|(\\d))T((\\d)|([0-1]\\d)|(2[0-4])):[0-5][0-9]:[0-5][0-9]"
                        }
                    ],
                    "formatString": "yyyy-MM-ddTHH:mm:ssK"
                }
            },
            "extractionType": "DateTime"
        }
    ],
    "inputs": [
        {
            "location": {
                "fileSystemLocations": {
                    "windowsFileTypeLogPaths": [
                        "C:\\Windows\\System32\\config\\systemprofile\\AppData\\Local\\Microsoft SQL Server IaaS Agent\\Assessment\\*.csv"
                    ]
                }
            },
            "recordDelimiter": {
                "regexDelimiter": {
                    "matchIndex": 0,
                    "pattern": "(^.*((\\d{2})|(\\d{4}))-([0-1]\\d)-(([0-3]\\d)|(\\d))T((\\d)|([0-1]\\d)|(2[0-4])):[0-5][0-9]:[0-5][0-9].*$)"
                }
            }
        }
    ]
}
