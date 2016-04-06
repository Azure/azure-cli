from . import TEST_DEF, load_test_definitions

load_test_definitions(
    package_name=locals()['__name__'],
    definition = [
        {
            'test_name': 'resource_group_list',
            'command': 'resource group list --output json'
        }
    ]
)
