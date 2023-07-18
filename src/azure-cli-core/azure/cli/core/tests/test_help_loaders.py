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


class JsonLoaderMixin(object):
    """A class containing helper methods for Json Loaders."""

    # get the list of json help file names for the command or group
    @staticmethod
    def _get_json_help_files_list(nouns, cmd_loader_map_ref):
        import inspect
        import os

        command_nouns = " ".join(nouns)
        # if command in map, get the loader. Path of loader is path of helpfile.
        ldr_or_none = cmd_loader_map_ref.get(command_nouns, [None])[0]
        if ldr_or_none:
            loaders = {ldr_or_none}
        else:
            loaders = set()

        # otherwise likely a group, try to find all command loaders under group as the group help could be defined
        # in either.
        if not loaders:
            for cmd_name, cmd_ldr in cmd_loader_map_ref.items():
                # if first word in loader name is the group, this is a command in the command group
                if cmd_name.startswith(command_nouns + " "):
                    loaders.add(cmd_ldr[0])

        results = []
        if loaders:
            for loader in loaders:
                loader_file_path = inspect.getfile(loader.__class__)
                dir_name = os.path.dirname(loader_file_path)
                files = os.listdir(dir_name)
                for file in files:
                    if file.endswith("help.json"):
                        help_file_path = os.path.join(dir_name, file)
                        results.append(help_file_path)
        return results

    @staticmethod
    def _parse_json_from_string(text, help_file_path):
        import os
        import json

        dir_name, base_name = os.path.split(help_file_path)
        pretty_file_path = os.path.join(os.path.basename(dir_name), base_name)

        if not text:
            raise CLIError("No content passed for {}.".format(pretty_file_path))

        try:
            return json.loads(text)
        except ValueError as e:
            raise CLIError("Error parsing {}:\n\n{}".format(pretty_file_path, e))


# test Help Loader, loads from help.json
class DummyHelpLoader(HelpLoaderV1, JsonLoaderMixin):
    # This loader has different keys in the data object. Except for "arguments" and "examples".
    core_attrs_to_keys = [("short_summary", "short"), ("long_summary", "long")]
    body_attrs_to_keys = core_attrs_to_keys + [("links", "hyper-links")]
    param_attrs_to_keys = core_attrs_to_keys + [("value_sources", "sources")]

    @property
    def version(self):
        return 2

    def get_noun_help_file_names(self, nouns):
        cmd_loader_map_ref = self.help_ctx.cli_ctx.invocation.commands_loader.cmd_to_loader_map
        return self._get_json_help_files_list(nouns, cmd_loader_map_ref)

    def update_file_contents(self, file_contents):
        for file_name in file_contents:
            if file_name not in self._file_content_dict:
                data_dict = {file_name: self._parse_json_from_string(file_contents[file_name], file_name)}
                self._file_content_dict.update(data_dict)

    def load_entry_data(self, help_obj, parser):
        prog = parser.prog if hasattr(parser, "prog") else parser._prog_prefix  # pylint: disable=protected-access
        command_nouns = prog.split()[1:]
        cmd_loader_map_ref = self.help_ctx.cli_ctx.invocation.commands_loader.cmd_to_loader_map

        files_list = self._get_json_help_files_list(command_nouns, cmd_loader_map_ref)
        data_list = [self._file_content_dict[name] for name in files_list]

        self._entry_data = self._get_entry_data(help_obj.command, data_list)

    def load_help_body(self, help_obj):
        self._update_obj_from_data_dict(help_obj, self._entry_data, self.body_attrs_to_keys)
