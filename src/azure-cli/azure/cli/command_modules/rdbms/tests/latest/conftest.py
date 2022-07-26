# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

mysql_location = None
postgres_location = None
resource_random_name = None


def pytest_addoption(parser):
    parser.addoption("--mysql-location", action="store", default="eastus2euap")
    parser.addoption("--postgres-location", action="store", default="eastus2euap")
    parser.addoption("--resource-random-name", action="store", default="clirecording")


def pytest_configure(config):
    global mysql_location, postgres_location, resource_random_name  # pylint:disable=global-statement
    mysql_location = config.getoption('--mysql-location')
    postgres_location = config.getoption('--postgres-location')
    resource_random_name = config.getoption('--resource-random-name')
