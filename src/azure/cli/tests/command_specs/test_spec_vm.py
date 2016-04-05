from . import TEST_DEF, load_test_definitions

load_test_definitions(
    package_name=locals()['__name__'],
    definition=[
        {
            'test_name': 'vm_usage_list_westus',
            'command': 'vm usage list --location westus --output json',
        }
    ]
)
