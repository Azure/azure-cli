import os
import re
import json
import pkgutil
from importlib import import_module

from PyInstaller.utils.hooks import collect_submodules

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
SRC_DIR = os.path.join(BASE_DIR, 'src')
PATTERN = r'operations_tmpl=(?P<quote>[\'"])(?P<module>.+)#.+(?P=quote)'
EXCLUDE_SUFFIX = ['.{}', '.operations']

_hiddenimports = [] # collect_submodules('win32ctypes')
modules = []

mods_ns_pkg = import_module('azure.cli.command_modules')
command_modules = [modname for _, modname, _ in pkgutil.iter_modules(mods_ns_pkg.__path__)]
for command_module in command_modules:
    print(command_module)
    _hiddenimports.extend(collect_submodules('azure.cli.command_modules.{}'.format(command_module)))

'''
for root, dirs, files in os.walk(SRC_DIR):
    for name in files:
        if name.endswith('.py') and not name.startswith('test_'):
            filepath = os.path.join(root, name)
            try:
                with open(filepath, 'r') as fp:
                    content = fp.read()
                    for match in re.finditer(PATTERN, content):
                        module = match.group('module')
                        for suffix in EXCLUDE_SUFFIX:
                            if module.endswith(suffix):
                                module = module[:-1*len(suffix)]
                        if module.startswith('azure.multiapi'):
                            module = 'azure.multiapi'
                        if module.startswith('azure.cli.command_modules.storage'):
                            continue
                        if module not in modules:
                            modules.append(module)
            except UnicodeDecodeError as e:
                print('ERROR: {}'.format(filepath))
print(json.dumps(modules, indent=4))


for module in modules:
    if module == 'custom':
        continue
    print('handling {}'.format(module))
    if module.endswith('.custom'):
        _hiddenimports.append(module)
    _hiddenimports.extend(collect_submodules(module))
print('handle done')
'''
hiddenimports = _hiddenimports
