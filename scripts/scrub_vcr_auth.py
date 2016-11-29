# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
import os
import tempfile

COMMAND_MODULE_PREFIX = 'azure-cli-'
PATH_TO_COMMAND_MODULES = os.path.abspath(os.path.join(os.path.abspath(__file__),
                                                       '..', '..', 'src',#'..', '..', '..', '..',
                                                       'command_modules'))
command_modules = []
insecure_cassettes = []
for name in os.listdir(PATH_TO_COMMAND_MODULES):
    full_module_path = os.path.join(PATH_TO_COMMAND_MODULES, name)
    if name.startswith(COMMAND_MODULE_PREFIX) and os.path.isdir(full_module_path):
        command_modules += [(name, full_module_path)]

    for name, fullpath in command_modules:
        path_to_recordings = os.path.join(fullpath, 'azure', 'cli', 'command_modules',
                                          name.replace(COMMAND_MODULE_PREFIX, ''),
                                          'tests', 'recordings')
        if not os.path.isdir(path_to_recordings):
            continue

        for name in os.listdir(path_to_recordings):
            if not str.endswith(name, '.yaml'):
                continue
            src_path = os.path.join(path_to_recordings, name)
            t = tempfile.NamedTemporaryFile('r+')
            with open(src_path, 'r') as f:
                for line in f:
                    if 'authorization: [bearer' in line.lower():
                        insecure_cassettes.append(name)
                    else:
                        t.write(line)
            t.seek(0)
            with open(src_path, 'w') as f:
                for line in t:
                    f.write(line)
            t.close()

insecure_cassettes = list(set(insecure_cassettes))
if insecure_cassettes:
    print('Bearer tokens removed from the following cassettes:')
    for cassette in insecure_cassettes:
        print('\t{}'.format(cassette))
else:
    print('All cassettes free from Bearer tokens!')
