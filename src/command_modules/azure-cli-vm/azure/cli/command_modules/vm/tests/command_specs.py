TEST_SPECS = [
    {
        'test_name': 'vm_usage_list_westus',
        'command': 'vm usage list --location westus --output json --disable-version-check',
        'expected_result': """[
  {
    "currentValue": 0,
    "limit": 2000,
    "name": {
      "localizedValue": "Availability Sets",
      "value": "availabilitySets"
    },
    "unit": "Count"
  },
  {
    "currentValue": 0,
    "limit": 100,
    "name": {
      "localizedValue": "Total Regional Cores",
      "value": "cores"
    },
    "unit": "Count"
  },
  {
    "currentValue": 0,
    "limit": 10000,
    "name": {
      "localizedValue": "Virtual Machines",
      "value": "virtualMachines"
    },
    "unit": "Count"
  },
  {
    "currentValue": 0,
    "limit": 50,
    "name": {
      "localizedValue": "Virtual Machine Scale Sets",
      "value": "virtualMachineScaleSets"
    },
    "unit": "Count"
  }
]
"""
    },
]
