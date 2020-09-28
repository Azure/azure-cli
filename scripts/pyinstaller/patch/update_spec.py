# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import json
import importlib
import pkgutil

SPEC_PATH = 'az.spec'

AZURE_CLI_SETUPS_PATH = {
    'azure-cli': 'src/azure-cli/setup.py',
    'azure-cli-core': 'src/azure-cli-core/setup.py'
}
START_FLAG = 'PACKAGE_DATA ='
END_FLAG = '}'

package_data = {}
datas = []
for package, path in AZURE_CLI_SETUPS_PATH.items():
    with open(path, 'r') as fp:
        content = fp.read()
        start = content.index(START_FLAG) + len(START_FLAG)
        end = content.index(END_FLAG, start) + len(END_FLAG)
        package_data[package] = json.loads(content[start:end].strip().replace('\'', '"'))

for package, data in package_data.items():
    for module, files in data.items():
        module_path = module.replace('.', '/')
        for f in files:
            filepath = os.path.join('src', package, module_path, f)
            target_path = os.path.dirname(os.path.join(module_path, f))
            datas.append('(\'{}\', \'{}\'),'.format(filepath, target_path))

with open(SPEC_PATH, 'r') as fp:
    content = fp.read()
with open(SPEC_PATH, 'w') as fp:
    fp.write(content.replace('\'ALL_PACKAGE_DATA\'', str('\n'.join(datas))))