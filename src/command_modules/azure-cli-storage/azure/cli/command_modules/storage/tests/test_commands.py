import os
import unittest
import yaml
from azure.cli.utils.command_test_util import CommandTestGenerator
from command_specs import TEST_DEF, ENV_VAR

class TestCommands(unittest.TestCase):
    pass

recording_dir = os.path.join(os.path.dirname(__file__), 'recordings')

def _truncate_long_running_operation(data):
    lro_item = data[0]
    for item in data[1:]:
        method = item['request'].get('method')
        code = item['response']['status'].get('code')
        if method == 'GET' and code == 202:
            print('METHOD: {} CODE: {} - IGNORING PART OF LRO'.format(method, code))
            data.remove(item)
        elif method == 'GET' and code == 200:
            print('METHOD: {} CODE: {} - FINAL RESULT OF LRO!'.format(method, code))
            lro_item['response'] = item['response']
            data.remove(item)
            return

def _shorten_long_running_operations(test_name):
    ''' In each YAML file, look for PUT requests with a code 202 response.
    These should be followed by a series of GET requests that finally end in a code 200 response.
    Replace the reponse of the intial PUT with the final code 200 response and delete all of the
    interim requests. '''
    print('Time compressing long running operations for {}...'.format(test_name))
    yaml_path = os.path.join(recording_dir, '{}.yaml'.format(test_name))
    with open(yaml_path, 'r+b') as f:
        data = yaml.load(f)['interactions']
        processed = []
        for item in data:
            method = item['request'].get('method')
            code = item['response']['status'].get('code')
            if method == 'PUT' and code == 202:
                print('METHOD: {} CODE: {} - TRUNCATE!!!'.format(method, code))
                _truncate_long_running_operation(data)
            else:
                print('METHOD: {} CODE: {} - OK Move to Processed'.format(method, code))
                processed.append(item)
                data.remove(item)
        f.seek(0)
        f.write(yaml.dump(data))
        f.truncate()

generator = CommandTestGenerator(recording_dir, TEST_DEF, ENV_VAR)
tests = generator.generate_tests()

for test_name in tests:
    _shorten_long_running_operations(test_name)
    setattr(TestCommands, test_name, tests[test_name])

if __name__ == '__main__':
    unittest.main()
