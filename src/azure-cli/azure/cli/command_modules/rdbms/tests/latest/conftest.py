import pytest

mysql_location = None
postgres_location = None

def pytest_addoption(parser):
    parser.addoption("--mysql-location", action="store", default="eastus2euap")
    parser.addoption("--postgres-location", action="store", default="eastus2euap")

def pytest_configure(config):
    global mysql_location, postgres_location
    mysql_location = config.getoption('--mysql-location')
    postgres_location = config.getoption('--postgres-location')
