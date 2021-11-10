import importlib
import os
from ._utils import _get_profile_module


class AAZCommandGroup:
    """Atomic Layer Command Group"""
    AZ_NAME = None


class AAZCommand:
    """Atomic Layer Command"""
    AZ_NAME = None


def register_command_group(name):
    """register AAZCommandGroup"""
    def decorator(cls):
        assert issubclass(cls, AAZCommandGroup)
        cls.AZ_NAME = name
        return cls
    return decorator


def register_command(name):
    """register AAZCommand"""
    def decorator(cls):
        assert issubclass(cls, AAZCommand)
        cls.AZ_NAME = name
        return cls
    return decorator


def load_aaz_command_table(aaz_module_name, cloud, args):
    modules = [_get_profile_module(aaz_module_name, cloud)]
    command_table = {}
    command_group_table = {}
    arg_str = ' '.join(args)
    idx = 0
    while idx < len(modules):
        module = modules[idx]
        sub_commands = {}
        cut = False  # if cut, its sub commands and sub modules will not be added
        for key, value in module.__dict__.items():
            if isinstance(value, type):
                if issubclass(value, AAZCommandGroup):
                    if not arg_str.startswith(f'{value.AZ_NAME} '):
                        cut = True
                    command_group_table[value.AZ_NAME] = value  # add command group even it's cut
                elif issubclass(value, AAZCommand):
                    if value.AZ_NAME:
                        sub_commands[value.AZ_NAME] = value
        if not cut:
            command_table.update(sub_commands)
            # for key in sub_commands:
            #     print(f"add Command {key}")
            module_path = os.path.dirname(module.__file__)
            for sub_path in os.listdir(module_path):
                if sub_path.startswith('_') or not os.path.isdir(os.path.join(module_path, sub_path)):
                    continue
                try:
                    mod = importlib.import_module(f'.{sub_path}', module.__name__)
                    modules.append(mod)
                except ModuleNotFoundError:
                    continue
        idx += 1
    return command_table, command_group_table

