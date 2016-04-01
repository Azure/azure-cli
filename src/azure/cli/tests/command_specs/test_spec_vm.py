definition = [
    {
        'test_name': 'vm_usage_list_westus',
        'command': 'vm usage list --location westus --output json',
    }
]


from . import TEST_DEF
package_name = locals()['__name__']

for i in definition:
    d = dict((k, i[k]) for k in i.keys() if k in ['test_name', 'command'])
    test_key = '{}.{}'.format(package_name, d['test_name'])
    TEST_DEF.append((test_key, d))
