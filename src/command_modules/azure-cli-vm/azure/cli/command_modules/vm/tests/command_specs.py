# AZURE CLI VM TEST DEFINITIONS

ENV_VAR = {}

TEST_DEF = [
    {
        'test_name': 'vm_usage_list_westus',
        'command': 'vm usage list --location westus --output json',
    }
]
