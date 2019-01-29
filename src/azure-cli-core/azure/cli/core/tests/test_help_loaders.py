# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError

from azure.cli.core import AzCommandsLoader
from azure.cli.core._help_loaders import HelpLoaderV1


# region TestCommandLoader
class TestCommandLoader(AzCommandsLoader):

    def __init__(self, cli_ctx=None):
        from azure.cli.core.commands import CliCommandType
        compute_custom = CliCommandType(
            operations_tmpl='{}#{{}}'.format(__name__),
        )
        super(TestCommandLoader, self).__init__(cli_ctx=cli_ctx,
                                                custom_command_type=compute_custom)
        self.cmd_to_loader_map = {}

    def load_command_table(self, args):
        with self.command_group('test') as g:
            g.custom_command('alpha', 'dummy_handler')

        return self.command_table

    def load_arguments(self, command):
        with self.argument_context('test') as c:
            c.argument('arg1', options_list=['--arg1', '-a'])
            c.argument('arg2', options_list=['--arg2', '-b'], help="Help From code.")
        with self.argument_context('test alpha') as c:
            c.positional('arg4', metavar="ARG4")
        self._update_command_definitions()  # pylint: disable=protected-access


def dummy_handler(arg1, arg2=None, arg3=None, arg4=None):
    """
    Short summary here. Long summary here. Still long summary.
    :param arg1: arg1's docstring help text
    :param arg2: arg2's docstring help text
    :param arg3: arg3's docstring help text
    :param arg4: arg4's docstring help text
    """
    pass


COMMAND_LOADER_CLS = TestCommandLoader

# region Test Help Loader


# test Help Loader, loads from help.json
class TestHelpLoader(HelpLoaderV1):
    # This loader has different keys in the data object. Except for "arguments" and "examples".
    core_attrs_to_keys = [("short_summary", "short"), ("long_summary", "long")]
    body_attrs_to_keys = core_attrs_to_keys + [("links", "hyper-links")]
    param_attrs_to_keys = core_attrs_to_keys + [("value_sources", "sources")]

    @property
    def version(self):
        return 2

    def load_raw_data(self, help_obj, parser):
        prog = parser.prog if hasattr(parser, "prog") else parser._prog_prefix
        command_nouns = prog.split()[1:]
        cmd_loader_map_ref = self.help_ctx.cli_ctx.invocation.commands_loader.cmd_to_loader_map
        all_data = self.get_json_help_for_nouns(command_nouns, cmd_loader_map_ref)
        self._data = self._get_entry_data(help_obj.command, all_data)

    def load_help_body(self, help_obj):
        self._update_obj_from_data_dict(help_obj, self._data, self.body_attrs_to_keys)

    # get the json help
    @staticmethod
    def get_json_help_for_nouns(nouns, cmd_loader_map_ref):
        import inspect
        import os

        def _parse_json_from_string(text, help_file_path):
            import json

            dir_name, base_name = os.path.split(help_file_path)

            pretty_file_path = os.path.join(os.path.basename(dir_name), base_name)

            try:
                data = json.loads(text)
                if not data:
                    raise CLIError("Error: Help file {} is empty".format(pretty_file_path))
                return data
            except ValueError as e:
                raise CLIError("Error parsing {}:\n\n{}".format(pretty_file_path, e))

        command_nouns = " ".join(nouns)
        # if command in map, get the loader. Path of loader is path of helpfile.
        loader = cmd_loader_map_ref.get(command_nouns, [None])[0]

        # otherwise likely a group, get the loader
        if not loader:
            for k, v in cmd_loader_map_ref.items():
                # if loader name starts with noun / group, this is a command in the command group
                if k.startswith(command_nouns):
                    loader = v[0]
                    break

        if loader:
            loader_file_path = inspect.getfile(loader.__class__)
            dir_name = os.path.dirname(loader_file_path)
            files = os.listdir(dir_name)
            for file in files:
                if file.endswith("help.json"):
                    help_file_path = os.path.join(dir_name, file)
                    with open(help_file_path, "r") as f:
                        text = f.read()
                        return [_parse_json_from_string(text, help_file_path)]
        return None
