__all__ = [
    'test_spec_network',
    'test_spec_resource',
    'test_spec_vm',
    'test_spec_storage',
    'test_spec_account'
]

# Declare test definitions in the definition portion of each test file
TEST_DEF = []

def load_test_definitions(package_name, definition):
    for i in definition:
        d = dict((k, i[k]) for k in i.keys() if k in ['test_name', 'command'])
        test_key = '{}.{}'.format(package_name, d['test_name'])
        TEST_DEF.append((test_key, d))