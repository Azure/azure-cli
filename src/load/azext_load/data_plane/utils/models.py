# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from enum import Enum


class IdentityType(str, Enum):
    SystemAssigned = "SystemAssigned"
    UserAssigned = "UserAssigned"


class EngineIdentityType(str, Enum):
    SystemAssigned = "SystemAssigned"
    UserAssigned = "UserAssigned"
    NoneValue = "None"


class AllowedFileTypes(str, Enum):
    ADDITIONAL_ARTIFACTS = "ADDITIONAL_ARTIFACTS"
    JMX_FILE = "JMX_FILE"
    USER_PROPERTIES = "USER_PROPERTIES"
    ZIPPED_ARTIFACTS = "ZIPPED_ARTIFACTS"
    URL_TEST_CONFIG = "URL_TEST_CONFIG"
    TEST_SCRIPT = 'TEST_SCRIPT'


class AllowedIntervals(str, Enum):
    PT10S = "PT10S"
    PT1H = "PT1H"
    PT1M = "PT1M"
    PT5M = "PT5M"
    PT5S = "PT5S"


class AllowedMetricNamespaces(str, Enum):
    LoadTestRunMetrics = "LoadTestRunMetrics"
    EngineHealthMetrics = "EngineHealthMetrics"


class AllowedTestTypes(str, Enum):
    JMX = "JMX"
    URL = "URL"
    LOCUST = "Locust"


class AllowedTestPlanFileExtensions(str, Enum):
    JMX = ".jmx"
    URL = ".json"
    LOCUST = ".py"


class AllowedTrendsResponseTimeAggregations(str, Enum):
    MEAN = "MEAN"
    MEDIAN = "MEDIAN"
    MAX = "MAX"
    MIN = "MIN"
    P75 = "P75"
    P90 = "P90"
    P95 = "P95"
    P96 = "P96"
    P98 = "P98"
    P99 = "P99"
    P999 = "P999"
    P9999 = "P9999"
