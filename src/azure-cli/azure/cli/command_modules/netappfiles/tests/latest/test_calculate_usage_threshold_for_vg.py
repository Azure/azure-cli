# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.command_modules.netappfiles.custom import calculate_usage_threshold, VolumeType


def test_calculate_usage_threshold_with_volume_type_data():
    # 100GiB data volume and default 50% additional capacity for snapshots returns bytes for 150GiB = 161061273600 bytes
    size = calculate_usage_threshold(100, VolumeType.DATA)
    assert size == 161061273600
    # 10GiB data volume returns the minimum, 100GiB = 107374182400 bytes
    size = calculate_usage_threshold(10, VolumeType.DATA)
    assert size == 107374182400


def test_calculate_usage_threshold_with_volume_type_log():
    # Memory > 512 for log volume returns bytes for 512GiB = 549755813888 bytes
    size = calculate_usage_threshold(550, VolumeType.LOG)
    assert size == 549755813888
    # Memory < 512 for log volume returns bytes for 50% of memory in bytes, 250GiB = 268435456000 bytes
    size = calculate_usage_threshold(500, VolumeType.LOG)
    assert size == 268435456000
    # Memory < 512 for log volume and lower than minimum size returns the minimum, 100GiB = 107374182400 bytes
    size = calculate_usage_threshold(10, VolumeType.LOG)
    assert size == 107374182400


def test_calculate_usage_threshold_with_volume_type_shared():
    # 900GiB shared volume with 2 hosts returns 1125 GiB = 1207959552000 ((TotalNumberOfHosts+3)/4)) * Memory)
    size = calculate_usage_threshold(900, VolumeType.SHARED, total_host_count=2)
    assert size == 1207959552000
    # 1030GiB shared volume with default 1 host returns 1030GiB = 1105954078720
    size = calculate_usage_threshold(1030, VolumeType.SHARED)
    assert size == 1105954078720
    # 100GB shared volume and default number of hosts return the minimum, 1024 GiB = 1099511627776
    size = calculate_usage_threshold(100, VolumeType.SHARED)
    assert size == 1099511627776


def test_calculate_usage_threshold_with_volume_type_data_backup():
    # 60GiB data volume and 50GiB log volume returns the combined sizes, 110GiB = 118111600640 bytes
    size = calculate_usage_threshold(0, VolumeType.DATA_BACKUP, data_size=64424509440, log_size=53687091200)
    assert size == 118111600640
    # 49GiB data volume and 50GiB log volume returns the minimum, 100GiB = 107374182400 bytes
    size = calculate_usage_threshold(0, VolumeType.DATA_BACKUP, data_size=52613349376, log_size=53687091200)
    assert size == 107374182400


def test_calculate_usage_threshold_with_volume_type_log_backup():
    # LOG BACKUP always returns 512GiB = 549755813888 bytes
    size = calculate_usage_threshold(0, VolumeType.LOG_BACKUP)
    assert size == 549755813888
    size = calculate_usage_threshold(100, VolumeType.LOG_BACKUP)
    assert size == 549755813888
    size = calculate_usage_threshold(1024, VolumeType.LOG_BACKUP)
    assert size == 549755813888
