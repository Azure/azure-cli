RESOURCE_GROUP_NAME = 'travistestresourcegroup'
STORAGE_ACCOUNT_NAME = 'travistestresourcegr3014'

definition = [
    {
        'test_name': 'storage_account_usage',
        'command': 'storage account usage',
    },
    {
        'test_name': 'storage_account_list',
        'command': 'storage account list'
    },
    {
        'test_name': 'storage_account_check_name',
        'command': 'storage account check-name-availability --name teststorageomega'
    },
    {
        'test_name': 'storage_account_list_keys',
        'command': 'storage account list-keys --rg {} --account_name {}'
            .format(RESOURCE_GROUP_NAME, STORAGE_ACCOUNT_NAME)
    }
]

from . import TEST_DEF
package_name = locals()['__name__']

for i in definition:
    d = dict((k, i[k]) for k in i.keys() if k in ['test_name', 'command'])
    test_key = '{}.{}'.format(package_name, d['test_name'])
    TEST_DEF.append((test_key, d))