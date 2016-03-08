spec = [
    {
        'test_name': 'network_usage_list',
        'command': 'network usage list --location westus --output json',
        'expected_result': """[
  {
    "currentValue": 6,
    "limit": 50,
    "name": {
      "localizedValue": "Virtual Networks",
      "value": "VirtualNetworks"
    },
    "unit": "Count"
  },
  {
    "currentValue": 0,
    "limit": 20,
    "name": {
      "localizedValue": "Static Public IP Addresses",
      "value": "StaticPublicIPAddresses"
    },
    "unit": "Count"
  },
  {
    "currentValue": 0,
    "limit": 100,
    "name": {
      "localizedValue": "Network Security Groups",
      "value": "NetworkSecurityGroups"
    },
    "unit": "Count"
  },
  {
    "currentValue": 1,
    "limit": 60,
    "name": {
      "localizedValue": "Public IP Addresses",
      "value": "PublicIPAddresses"
    },
    "unit": "Count"
  },
  {
    "currentValue": 0,
    "limit": 300,
    "name": {
      "localizedValue": "Network Interfaces",
      "value": "NetworkInterfaces"
    },
    "unit": "Count"
  },
  {
    "currentValue": 0,
    "limit": 100,
    "name": {
      "localizedValue": "Load Balancers",
      "value": "LoadBalancers"
    },
    "unit": "Count"
  },
  {
    "currentValue": 0,
    "limit": 50,
    "name": {
      "localizedValue": "Application Gateways",
      "value": "ApplicationGateways"
    },
    "unit": "Count"
  },
  {
    "currentValue": 0,
    "limit": 100,
    "name": {
      "localizedValue": "Route Tables",
      "value": "RouteTables"
    },
    "unit": "Count"
  }
]
"""
    },
]

from . import TEST_SPECS
TEST_SPECS.append((locals()['__name__'], spec))
