from . import TEST_DEF, load_test_definitions

load_test_definitions(
    package_name=locals()['__name__'],
    definition = [
        {
            'test_name': 'network_usage_list',
            'command': 'network usage list --location westus --output json'
        },
        {
            'test_name': 'network_nic_list',
            'command': 'network nic list -g travistestresourcegroup'
        }
    ]
)
