# AZURE CLI NETWORK TEST DEFINITIONS

ENV_VAR = {}

TEST_DEF = [
    {
        'test_name': 'network_usage_list',
        'command': 'network list-usages --location westus --output json'
    },
    {
        'test_name': 'network_nic_list',
        'command': 'network nic list travistestresourcegroup'
    }
]

