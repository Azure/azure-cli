import importlib
import pkgutil

CORE_INIT_PATH = 'src/azure-cli-core/azure/cli/core/__init__.py'

mods_ns_pkg = importlib.import_module('azure.cli.command_modules')
command_modules = [modname for _, modname, _ in pkgutil.iter_modules(mods_ns_pkg.__path__)]

with open(CORE_INIT_PATH, 'r') as fp:
    content = fp.read()
with open(CORE_INIT_PATH, 'w') as fp:
    fp.write(content.replace('\'ALL_COMMAND_MODULES\'', str(command_modules)))