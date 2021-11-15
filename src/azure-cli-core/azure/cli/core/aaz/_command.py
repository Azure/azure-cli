import importlib
import os
from ._utils import _get_profile_pkg
from knack.commands import CLICommand, CommandGroup


class AAZCommandGroup:
    """Atomic Layer Command Group"""
    AZ_NAME = None

    def __init__(self, cli_ctx):
        self.cli_ctx = cli_ctx
        self.group_kwargs = {}


class AAZCommand(CLICommand):
    """Atomic Layer Command"""
    AZ_NAME = None

    def __init__(self, loader):
        self.loader = loader
        super(AAZCommand, self).__init__(
            cli_ctx=loader.cli_ctx,
            name=self.AZ_NAME,
            handler=self._handler,
            arguments_loader=self._arguments_loader,
            description_loader=self._description_loader,
        )
        self.command_kwargs = {}

    def _handler(self, *args, **kwargs):
        return None

    def _arguments_loader(self):
        """load arguments"""
        return {}

    def _description_loader(self):
        return f"This is command description for {self.AZ_NAME}"

    def __call__(self, *args, **kwargs):
        return self.handler(*args, **kwargs)


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


def load_aaz_command_table(loader, aaz_pkg_name, args):
    profile_pkg = _get_profile_pkg(aaz_pkg_name, loader.cli_ctx.cloud)
    pkgs = [profile_pkg]
    command_table = {}
    command_group_table = {}
    arg_str = ' '.join(args)
    idx = 0
    while idx < len(pkgs):
        pkg = pkgs[idx]
        cut = False  # if cut, its sub commands and sub pkgs will not be added
        for key, value in pkg.__dict__.items():
            if isinstance(value, type):
                if issubclass(value, AAZCommandGroup):
                    if not arg_str.startswith(f'{value.AZ_NAME} '):
                        cut = True
                    # add command group into command group table
                    command_group_table[value.AZ_NAME] = value(cli_ctx=loader.cli_ctx)  # add command group even it's cut
                elif issubclass(value, AAZCommand):
                    if value.AZ_NAME:
                        command_table[value.AZ_NAME] = value(loader=loader)
        if not cut:
            # continue load sub pkgs
            pkg_path = os.path.dirname(pkg.__file__)
            for sub_path in os.listdir(pkg_path):
                if sub_path.startswith('_') or not os.path.isdir(os.path.join(pkg_path, sub_path)):
                    continue
                try:
                    pkg = importlib.import_module(f'.{sub_path}', pkg.__name__)
                    pkgs.append(pkg)
                except ModuleNotFoundError:
                    continue
        idx += 1

    for group_name, command_group in command_group_table.items():
        loader.command_group_table[group_name] = command_group
    for command_name, command in command_table.items():
        loader.command_table[command_name] = command
    return command_table, command_group_table

