# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

mysql_location = None
mysql_paired_location = None
mysql_general_purpose_sku = None
mysql_memory_optimized_sku = None
postgres_location = None
resource_random_name = None


def pytest_addoption(parser):
    parser.addoption("--mysql-location", action="store", default="eastus2euap")
    parser.addoption("--mysql-paired-location", action="store", default="centraluseuap")
    parser.addoption("--mysql-general-purpose-sku", action="store", default="Standard_D2s_v3")
    parser.addoption("--mysql-memory-optimized-sku", action="store", default="Standard_E2s_v3")
    parser.addoption("--postgres-location", action="store", default="eastus2euap")
    parser.addoption("--resource-random-name", action="store", default="clirecording")


def pytest_configure(config):
    global mysql_location, mysql_paired_location, mysql_general_purpose_sku, mysql_memory_optimized_sku, postgres_location, resource_random_name  # pylint:disable=global-statement
    mysql_location = config.getoption('--mysql-location')
    mysql_paired_location = config.getoption('--mysql-paired-location')
    mysql_general_purpose_sku = config.getoption('--mysql-general-purpose-sku')
    mysql_memory_optimized_sku = config.getoption('--mysql-memory-optimized-sku')
    postgres_location = config.getoption('--postgres-location')
    resource_random_name = config.getoption('--resource-random-name')