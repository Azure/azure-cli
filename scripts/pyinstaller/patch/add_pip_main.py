# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os

PIP_MAIN = '''
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import runpy


if __name__ == '__main__':
    runpy.run_module('pip', run_name='__main__')

'''

pip_main_path = 'src/pip'
if not os.path.exists(pip_main_path):
    os.mkdir(pip_main_path)
with open(os.path.join(pip_main_path, 'main.py'), 'w') as fp:
    fp.write(PIP_MAIN)
