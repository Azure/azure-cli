import importlib
import os
from ._utils import _get_profile_pkg
from knack.commands import CLICommand, CommandGroup

_DOC_EXAMPLE_FLAG = ':example:'


class AAZCommandGroup:
    """Atomic Layer Command Group"""
    AZ_NAME = None
    AZ_HELP = None

    def __init__(self, cli_ctx):
        self.cli_ctx = cli_ctx
        self.group_kwargs = {
            # 'deprecate_info'  # deprecate_info should be in group_kwargs
            # 'preview_info'
            # 'experimental_info'
        }
        self.help = self.AZ_HELP  # TODO: change knack to load help directly


class AAZCommand(CLICommand):
    """Atomic Layer Command"""
    AZ_NAME = None
    AZ_HELP = None

    def __init__(self, loader):
        self.loader = loader
        super(AAZCommand, self).__init__(
            cli_ctx=loader.cli_ctx,
            name=self.AZ_NAME,
            handler=self._handler,
            arguments_loader=self._arguments_loader,
        )
        self.command_kwargs = {}
        self.help = self.AZ_HELP
        # help property will be assigned as help_file for command parser https://github.com/Azure/azure-cli/blob/d69eedd89bd097306b8579476ef8026b9f2ad63d/src/azure-cli-core/azure/cli/core/parser.py#L104
        # help_file will be loaded as file_data in knack https://github.com/microsoft/knack/blob/e496c9590792572e680cb3ec959db175d9ba85dd/knack/help.py#L206-L208

    def _handler(self, *args, **kwargs):
        return None

    def _arguments_loader(self):
        """load arguments"""
        return {}

    def __call__(self, *args, **kwargs):
        return self.handler(*args, **kwargs)


def register_command_group(name):
    """register AAZCommandGroup"""
    def decorator(cls):
        import yaml
        from knack.help_files import helps
        assert issubclass(cls, AAZCommandGroup)
        cls.AZ_NAME = name
        short_summary, long_summary, _ = parse_cls_doc(cls)
        cls.AZ_HELP = {
            "type": "group",
            "short-summary": short_summary,
            "long-summary": long_summary
        }

        # the only way to load command group help in knack is by _load_from_file
        # TODO: change knack to load AZ_HELP directly
        helps[name] = yaml.safe_dump(cls.AZ_HELP)
        return cls
    return decorator


def register_command(name):
    """register AAZCommand"""
    def decorator(cls):
        assert issubclass(cls, AAZCommand)
        cls.AZ_NAME = name
        short_summary, long_summary, examples = parse_cls_doc(cls)
        cls.AZ_HELP = {
            "type": "command",
            "short-summary": short_summary,
            "long-summary": long_summary,
            "examples": examples
        }
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
                    sub_pkg = importlib.import_module(f'.{sub_path}', pkg.__name__)
                    pkgs.append(sub_pkg)
                except ModuleNotFoundError:
                    continue
        idx += 1

    for group_name, command_group in command_group_table.items():
        loader.command_group_table[group_name] = command_group
    for command_name, command in command_table.items():
        loader.command_table[command_name] = command
    return command_table, command_group_table


def parse_cls_doc(cls):
    doc = cls.__doc__
    short_summary = None
    long_summary = None
    lines = []
    if doc:
        for line in doc.splitlines():
            l = line.strip()
            if l:
                lines.append(l)
    examples = []
    if lines:
        short_summary = lines[0]
        assert not short_summary.startswith(':')
        idx = 1
        while idx < len(lines):
            line = lines[idx]
            if line.startswith(_DOC_EXAMPLE_FLAG):
                break
            idx += 1
        long_summary = '\n'.join(lines[1:idx]) or None
        while idx < len(lines):
            line = lines[idx]
            if line.startswith(_DOC_EXAMPLE_FLAG):
                example = {
                    "name": line[len(_DOC_EXAMPLE_FLAG):].strip()
                }
                e_idx = idx + 1
                while e_idx < len(lines) and not lines[e_idx].startswith(_DOC_EXAMPLE_FLAG):
                    e_idx += 1
                example["text"] = ' '.join(lines[idx+1: e_idx]) or None
                if example["text"]:
                    examples.append(example)
                idx = e_idx - 1
            idx += 1
    return short_summary, long_summary, examples
