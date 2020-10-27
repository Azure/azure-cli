# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import os
import json
import traceback


class TestData:
    """
    Model for testing results
    """
    def __init__(self, artifact_dir):
        # Value of the list should be (module_name, passed, failed, pass_rate)
        self.modules = []
        # ('Total', passed, failed, pass_rate)
        self.total = None
        self.artifact_dir = artifact_dir

    def collect(self):
        """
        Collect data
        :return:
        """
        print('Generating summary...')
        data_dict = {}
        for root, dirs, files in os.walk(self.artifact_dir):
            for name in files:
                if name.endswith('json'):
                    try:
                        print('Reading {}'.format(name))
                        module = name.split('.')[0]
                        with open(os.path.join(root, name)) as f:
                            result = json.loads(f.read())
                            passed = failed = 0
                            if 'passed' in result['summary']:
                                passed = result['summary']['passed']
                            if 'failed' in result['summary']:
                                failed = result['summary']['failed']
                            if module in data_dict:
                                values = data_dict[module]
                                data_dict[module] = (values[0] + passed, values[1] + failed)
                            else:
                                data_dict[module] = (passed, failed)
                    except Exception:
                        print(traceback.format_exc())

        passed_sum = failed_sum = 0
        for k in data_dict:
            v = data_dict[k]
            passed = v[0]
            failed = v[1]
            total = passed + failed
            rate = 1 if total == 0 else passed / total
            rate = '{:.2%}'.format(rate)
            self.modules.append((k, passed, failed, rate))
            print('module: {}, passed: {}, failed: {}, rate: {}'.format(k, passed, failed, rate))
            passed_sum += passed
            failed_sum += failed

        print(self.modules)
        print('Sorting...')
        sorted_modules = sorted(self.modules, key=lambda x: x[0])
        self.modules = sorted_modules
        print(self.modules)

        total_sum = passed_sum + failed_sum
        rate_sum = 1 if total_sum == 0 else passed_sum / total_sum
        rate_sum = '{:.2%}'.format(rate_sum)
        self.total = ('Total', passed_sum, failed_sum, rate_sum)
        print('module: Total, passed: {}, failed: {}, rate: {}'.format(passed_sum, failed_sum, rate_sum))
