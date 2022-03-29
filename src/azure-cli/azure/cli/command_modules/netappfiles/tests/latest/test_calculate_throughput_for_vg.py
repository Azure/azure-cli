from azure.cli.command_modules.netappfiles.custom import VolumeType, calculate_throughput


def test_data_volume_throughput_calculation():
    # 0-1TiB should return 400MiB/s
    throughput = calculate_throughput(1023, VolumeType.DATA)
    assert throughput == 400
    throughput = calculate_throughput(1024, VolumeType.DATA)
    assert throughput == 400

    # 1-2TiB should return 600MiB/s
    throughput = calculate_throughput(1025, VolumeType.DATA)
    assert throughput == 600
    throughput = calculate_throughput(2048, VolumeType.DATA)
    assert throughput == 600

    # 2-4TiB should return 800MiB/s
    throughput = calculate_throughput(2049, VolumeType.DATA)
    assert throughput == 800
    throughput = calculate_throughput(4096, VolumeType.DATA)
    assert throughput == 800

    # 4-6TiB should return 1000MiB/s
    throughput = calculate_throughput(4097, VolumeType.DATA)
    assert throughput == 1000
    throughput = calculate_throughput(6144, VolumeType.DATA)
    assert throughput == 1000

    # 6-8TiB should return 1200MiB/s
    throughput = calculate_throughput(6145, VolumeType.DATA)
    assert throughput == 1200
    throughput = calculate_throughput(8192, VolumeType.DATA)
    assert throughput == 1200

    # 8-10TiB should return 1400MiB/s
    throughput = calculate_throughput(8193, VolumeType.DATA)
    assert throughput == 1400
    throughput = calculate_throughput(10248, VolumeType.DATA)
    assert throughput == 1400

    # >10TiB should return 1500MiB/s
    throughput = calculate_throughput(10249, VolumeType.DATA)
    assert throughput == 1500
    throughput = calculate_throughput(10000000, VolumeType.DATA)
    assert throughput == 1500


def test_calculate_throughput_for_log_volume():
    # 0-4TiB should return 250MiB/s
    throughput = calculate_throughput(1024, VolumeType.LOG)
    assert throughput == 250
    throughput = calculate_throughput(4096, VolumeType.LOG)
    assert throughput == 250
    # >4TiB should return 500MiB/s
    throughput = calculate_throughput(4097, VolumeType.LOG)
    assert throughput == 500
    throughput = calculate_throughput(10000, VolumeType.LOG)
    assert throughput == 500


def test_shared_volume_throughput_is_always_64():
    throughput = calculate_throughput(1, VolumeType.SHARED)
    assert throughput == 64
    throughput = calculate_throughput(1024, VolumeType.SHARED)
    assert throughput == 64
    throughput = calculate_throughput(10248, VolumeType.SHARED)
    assert throughput == 64


def test_data_backup_volume_throughput_is_always_128():
    throughput = calculate_throughput(1, VolumeType.DATA_BACKUP)
    assert throughput == 128
    throughput = calculate_throughput(1024, VolumeType.DATA_BACKUP)
    assert throughput == 128
    throughput = calculate_throughput(10248, VolumeType.DATA_BACKUP)
    assert throughput == 128


def test_log_backup_volume_throughput_is_always_250():
    throughput = calculate_throughput(1, VolumeType.LOG_BACKUP)
    assert throughput == 250
    throughput = calculate_throughput(1024, VolumeType.LOG_BACKUP)
    assert throughput == 250
    throughput = calculate_throughput(10248, VolumeType.LOG_BACKUP)
    assert throughput == 250

