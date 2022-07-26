# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import logging
import shutil
import inspect
from inspect import getmembers as inspect_getmembers

import unittest
from unittest import mock
import tempfile

from knack.help import GroupHelpFile, HelpAuthoringException
from azure.cli.core._help import CliCommandHelpFile

from azure.cli.core.mock import DummyCli
from azure.cli.core.commands import _load_command_loader
from azure.cli.core.file_util import get_all_help

logger = logging.getLogger(__name__)

# Command loader module
MOCKED_COMMAND_LOADER_MOD = "test_help_loaders"


# mock command loader method so that only the mock command loader can be loaded.
def mock_load_command_loader(loader, args, name, prefix):
    return _load_command_loader(loader, args, name, "azure.cli.core.tests.")


# mock inspect.getfile to discover directory containing help files.
def get_mocked_inspect_getfile(expected_arg, return_value):

    def inspect_getfile(obj):
        if obj == expected_arg:
            return return_value
        else:
            return inspect.getfile(obj)
    return inspect_getfile


# mock getmembers so test help loader can be injected into AzCliHelp class' versioned loader list
def mock_inspect_getmembers(object, predicate=None):
    import azure.cli.core.tests.test_help_loaders as possible_loaders

    if "azure.cli.core._help_loaders" in repr(object) and "is_loader_cls" in repr(predicate):
        result = inspect_getmembers(object, predicate)
        result.extend(inspect_getmembers(possible_loaders, predicate))
        return list(set(result))
    else:
        return inspect_getmembers(object, predicate)


def _store_parsers(parser, d):
    for s in parser.subparsers.values():
        d[_get_parser_name(s)] = s
        if _is_group(s):
            for c in s.choices.values():
                d[_get_parser_name(c)] = c
                _store_parsers(c, d)


def _is_group(parser):
    return getattr(parser, 'choices', None) is not None


def _get_parser_name(parser):
    # pylint:disable=protected-access
    return (parser._prog_prefix if hasattr(parser, '_prog_prefix') else parser.prog)[len('az '):]


def create_invoker_and_load_cmds_and_args(cli_ctx):
    from knack import events
    from azure.cli.core.commands import register_cache_arguments
    from azure.cli.core.commands.arm import register_global_subscription_argument, register_ids_argument

    invoker = cli_ctx.invocation_cls(cli_ctx=cli_ctx, commands_loader_cls=cli_ctx.commands_loader_cls,
                                     parser_cls=cli_ctx.parser_cls, help_cls=cli_ctx.help_cls)
    cli_ctx.invocation = invoker
    invoker.commands_loader.skip_applicability = True
    invoker.commands_loader.load_command_table(None)

    # Deal with failed import MainCommandsLoader.load_command_table._update_command_table_from_modules
    # during tox test.
    if not invoker.commands_loader.cmd_to_loader_map:
        module_command_table, module_group_table = mock_load_command_loader(invoker.commands_loader, None,
                                                                            MOCKED_COMMAND_LOADER_MOD, None)
        for cmd in module_command_table.values():
            cmd.command_source = MOCKED_COMMAND_LOADER_MOD
        invoker.commands_loader.command_table.update(module_command_table)
        invoker.commands_loader.command_group_table.update(module_group_table)

    # turn off applicability check for all loaders
    for loaders in invoker.commands_loader.cmd_to_loader_map.values():
        for loader in loaders:
            loader.skip_applicability = True

    for command in invoker.commands_loader.command_table:
        invoker.commands_loader.load_arguments(command)

    register_global_subscription_argument(cli_ctx)
    register_ids_argument(cli_ctx)  # global subscription must be registered first!
    register_cache_arguments(cli_ctx)
    cli_ctx.raise_event(events.EVENT_INVOKER_POST_CMD_TBL_CREATE, commands_loader=invoker.commands_loader)
    invoker.parser.load_command_table(invoker.commands_loader)


# TODO update this CLASS to properly load all help....
class HelpTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Ensure initialization has occurred correctly
        logging.basicConfig(level=logging.DEBUG)

    @classmethod
    def tearDownClass(cls):
        logging.shutdown()

    def test_help_loads(self):
        from azure.cli.core.commands.arm import register_global_subscription_argument, register_ids_argument
        import knack.events as events

        parser_dict = {}
        cli = DummyCli()
        help_ctx = cli.help_cls(cli)
        try:
            cli.invoke(['-h'])
        except SystemExit:
            pass
        cmd_tbl = cli.invocation.commands_loader.command_table
        cli.invocation.parser.load_command_table(cli.invocation.commands_loader)
        for cmd in cmd_tbl:
            try:
                cmd_tbl[cmd].loader.command_name = cmd
                cmd_tbl[cmd].loader.load_arguments(cmd)
            except KeyError:
                pass
        cli.register_event(events.EVENT_INVOKER_POST_CMD_TBL_CREATE, register_global_subscription_argument)
        cli.register_event(events.EVENT_INVOKER_POST_CMD_TBL_CREATE, register_ids_argument)
        cli.raise_event(events.EVENT_INVOKER_CMD_TBL_LOADED, command_table=cmd_tbl)
        cli.invocation.parser.load_command_table(cli.invocation.commands_loader)
        _store_parsers(cli.invocation.parser, parser_dict)

        # TODO: do we want to update this as it doesn't actually load all help.
        # We do have a CLI linter which does indeed load all help.
        for name, parser in parser_dict.items():
            try:
                help_file = GroupHelpFile(help_ctx, name, parser) if _is_group(parser) \
                    else CliCommandHelpFile(help_ctx, name, parser)
                help_file.load(parser)
            except Exception as ex:
                raise HelpAuthoringException('{}, {}'.format(name, ex))


class TestHelpLoads(unittest.TestCase):
    def setUp(self):
        from knack.help_files import helps
        self.test_cli = DummyCli()
        self.helps = helps
        self._tempdirName = tempfile.mkdtemp(prefix="help_test_temp_dir_")

    def tearDown(self):
        # delete temporary directory to be used for temp files.
        shutil.rmtree(self._tempdirName)
        self.helps.clear()

    def set_help_py(self):
        self.helps['test'] = """
            type: group
            short-summary: Foo Bar Group
            long-summary: Foo Bar Baz Group is a fun group
        """

        self.helps['test alpha'] = """
            type: command
            short-summary: Foo Bar Command
            long-summary: Foo Bar Baz Command is a fun command
            parameters:
                - name: --arg1 -a
                  short-summary: A short summary
                  populator-commands:
                  - az foo bar
                  - az bar baz
                - name: ARG4 # Note: positional's are discouraged in the CLI.
                  short-summary: Positional parameter. Not required
            examples:
                - name: Alpha Example
                  text: az test alpha --arg1 a --arg2 b --arg3 c
                  supported-profiles: 2018-03-01-hybrid, latest
                - name: A simple example unsupported on latest
                  text: az test alpha --arg1 a --arg2 b
                  unsupported-profiles: 2017-03-09-profile
        """

    def set_help_yaml(self):
        yaml_help = """
        version: 1
        content:
        - group:
            name: test
            summary: Group yaml summary
            description: Group yaml description. A.K.A long description
            links:
                - title: Azure Test Docs
                  url: "https://docs.microsoft.com/azure/test"
                - url: "https://aka.ms/just-a-url"
        - command:
            name: test alpha
            summary: Command yaml summary
            description: Command yaml description. A.K.A long description
            links:
                - title: Azure Test Alpha Docs
                  url: "https://docs.microsoft.com/azure/test/alpha"
                - url: "https://aka.ms/just-a-long-url"
            arguments:
                - name: --arg2 # we do not specify the short option in the name.
                  summary: Arg 2's summary
                  description: A true description of this parameter.
                  value-sources:
                    - string: "Number range: -5.0 to 5.0"
                    - link:
                        url: https://www.foo.com
                        title: foo
                    - link:
                        command: az test show
                        title: Show test details
                - name: ARG4  # Note: positional's are discouraged in the CLI.
                  summary: Arg4's summary, yaml. Positional arg, not required
            examples:
                - summary: A simple example
                  description: More detail on the simple example.
                  command: az test alpha --arg1 apple --arg2 ball --arg3 cat
                  supported-profiles: 2018-03-01-hybrid, latest
                - summary: Another example unsupported on latest
                  description: More detail on the unsupported example.
                  command: az test alpha --arg1 apple --arg2 ball
                  unsupported-profiles: 2017-03-09-profile
        """
        return self._create_new_temp_file(yaml_help, suffix="help.yaml")

    def set_help_json(self):
        json_help = """
            {
                "version": 2,
                "content": [
                    {
                        "group": {
                            "name": "test",
                            "short": "Group json summary",
                            "long": "Group json description. A.K.A long description",
                            "hyper-links": [
                                {
                                    "title": "Azure Json Test Docs",
                                    "url": "https://docs.microsoft.com/azure/test"
                                },
                                {
                                    "url": "https://aka.ms/just-a-url"
                                }
                            ]
                        }
                    },
                    {
                        "command": {
                            "name": "test alpha",
                            "short": "Command json summary",
                            "long": "Command json description. A.K.A long description",
                            "hyper-links": [
                                {
                                    "title": "Azure Json Test Alpha Docs",
                                    "url": "https://docs.microsoft.com/azure/test/alpha"
                                },
                                {
                                    "url": "https://aka.ms/just-a-long-url"
                                }
                            ],
                            "arguments": [
                                {
                                    "name": "--arg3",
                                    "short": "Arg 3's json summary",
                                    "long": "A truly true description of this parameter.",
                                    "sources": [
                                        {
                                            "string": "Number range: 0 to 10"
                                        },
                                        {
                                            "link": {
                                                "url": "https://www.foo-json.com",
                                                "title": "foo-json"
                                            }
                                        },
                                        {
                                            "link": {
                                                "command": "az test show",
                                                "title": "Show test details. Json file"
                                            }
                                        }
                                    ]
                                },
                                {
                                    "name": "ARG4",
                                    "summary": "Arg4's summary, json. Positional arg, not required"
                                }
                            ],
                            "examples": [
                                {
                                    "summary": "A simple example from json",
                                    "description": "More detail on the simple example.",
                                    "command": "az test alpha --arg1 alpha --arg2 beta --arg3 chi",
                                    "supported-profiles": "2018-03-01-hybrid, latest"
                                }
                            ]
                        }
                    }
                ]
            }
        """
        return self._create_new_temp_file(json_help, suffix="help.json")

    # Mock logic in core.MainCommandsLoader.load_command_table for retrieving installed modules.
    @mock.patch('pkgutil.iter_modules', side_effect=lambda x: [(None, MOCKED_COMMAND_LOADER_MOD, None)])
    @mock.patch('azure.cli.core.commands._load_command_loader', side_effect=mock_load_command_loader)
    def test_basic(self, mocked_load, mocked_pkg_util):
        with self.assertRaises(SystemExit):
            self.test_cli.invoke(["test", "alpha", "-h"])

    # Mock logic in core.MainCommandsLoader.load_command_table for retrieving installed modules.
    @mock.patch('pkgutil.iter_modules', side_effect=lambda x: [(None, MOCKED_COMMAND_LOADER_MOD, None)])
    @mock.patch('azure.cli.core.commands._load_command_loader', side_effect=mock_load_command_loader)
    def test_load_from_help_py(self, mocked_load, mocked_pkg_util):
        self.set_help_py()
        create_invoker_and_load_cmds_and_args(self.test_cli)
        group_help_obj = next((help for help in get_all_help(self.test_cli) if help.command == "test"), None)
        command_help_obj = next((help for help in get_all_help(self.test_cli) if help.command == "test alpha"), None)

        # Test that group and command help are successfully displayed.
        with self.assertRaises(SystemExit):
            self.test_cli.invoke(["test", "-h"])
        with self.assertRaises(SystemExit):
            self.test_cli.invoke(["test", "alpha", "-h"])

        # Test group help
        self.assertIsNotNone(group_help_obj)
        self.assertEqual(group_help_obj.short_summary, "Foo Bar Group.")
        self.assertEqual(group_help_obj.long_summary, "Foo Bar Baz Group is a fun group.")

        # Test command help
        self.assertIsNotNone(command_help_obj)
        self.assertEqual(command_help_obj.short_summary, "Foo Bar Command.")
        self.assertEqual(command_help_obj.long_summary, "Foo Bar Baz Command is a fun command.")

        # test that parameters and help are loaded from command function docstring, argument registry help and help.py
        obj_param_dict = {param.name: param for param in command_help_obj.parameters}
        param_name_set = {"--arg1 -a", "--arg2 -b", "--arg3", "ARG4"}
        self.assertTrue(set(obj_param_dict.keys()).issuperset(param_name_set))

        self.assertEqual(obj_param_dict["--arg3"].short_summary, "Arg3's docstring help text.")
        self.assertEqual(obj_param_dict["ARG4"].short_summary, "Positional parameter. Not required.")
        self.assertEqual(obj_param_dict["--arg1 -a"].short_summary, "A short summary.")

        self.assertEqual(obj_param_dict["--arg1 -a"].short_summary, "A short summary.")
        self.assertEqual(obj_param_dict["--arg1 -a"].value_sources[0]['link']['command'], "az foo bar")
        self.assertEqual(obj_param_dict["--arg1 -a"].value_sources[1]['link']['command'], "az bar baz")

        if self.test_cli.cloud.profile in ['2018-03-01-hybrid', 'latest']:
            self.assertEqual(command_help_obj.examples[0].short_summary, "Alpha Example")
            self.assertEqual(command_help_obj.examples[0].command, "az test alpha --arg1 a --arg2 b --arg3 c")
            self.assertEqual(command_help_obj.examples[0].supported_profiles, "2018-03-01-hybrid, latest")
            self.assertEqual(command_help_obj.examples[0].unsupported_profiles, None)

            self.assertEqual(command_help_obj.examples[1].supported_profiles, None)
            self.assertEqual(command_help_obj.examples[1].unsupported_profiles, "2017-03-09-profile")

        if self.test_cli.cloud.profile == '2019-03-01-hybrid':
            self.assertEqual(len(command_help_obj.examples), 1)
            self.assertEqual(command_help_obj.examples[0].short_summary, "A simple example unsupported on latest")
            self.assertEqual(command_help_obj.examples[0].command, "az test alpha --arg1 a --arg2 b")
            self.assertEqual(command_help_obj.examples[0].unsupported_profiles, '2017-03-09-profile')

        if self.test_cli.cloud.profile == '2017-03-09-profile':
            self.assertEqual(len(command_help_obj.examples), 0)

    @mock.patch('pkgutil.iter_modules', side_effect=lambda x: [(None, MOCKED_COMMAND_LOADER_MOD, None)])
    @mock.patch('azure.cli.core.commands._load_command_loader', side_effect=mock_load_command_loader)
    def test_load_from_help_yaml(self, mocked_load, mocked_pkg_util):
        # setup help.py and help.yaml help.
        self.set_help_py()
        yaml_path = self.set_help_yaml()
        create_invoker_and_load_cmds_and_args(self.test_cli)

        # mock logic in core._help_loaders for retrieving yaml file from loader path.
        expected_arg = self.test_cli.invocation.commands_loader.cmd_to_loader_map['test alpha'][0].__class__
        with mock.patch('inspect.getfile', side_effect=get_mocked_inspect_getfile(expected_arg, yaml_path)):
            group_help_obj = next((help for help in get_all_help(self.test_cli) if help.command == "test"), None)
            command_help_obj = next((help for help in get_all_help(self.test_cli) if help.command == "test alpha"), None)  # pylint: disable=line-too-long

            # Test that group and command help are successfully displayed.
            with self.assertRaises(SystemExit):
                self.test_cli.invoke(["test", "-h"])
            with self.assertRaises(SystemExit):
                self.test_cli.invoke(["test", "alpha", "-h"])

        # Test group help
        self.assertIsNotNone(group_help_obj)
        self.assertEqual(group_help_obj.short_summary, "Group yaml summary.")
        self.assertEqual(group_help_obj.long_summary, "Group yaml description. A.K.A long description.")
        self.assertEqual(group_help_obj.links[0], {"title": "Azure Test Docs", "url": "https://docs.microsoft.com/azure/test"})
        self.assertEqual(group_help_obj.links[1], {"url": "https://aka.ms/just-a-url"})

        # Test command help
        self.assertIsNotNone(command_help_obj)
        self.assertEqual(command_help_obj.short_summary, "Command yaml summary.")
        self.assertEqual(command_help_obj.long_summary, "Command yaml description. A.K.A long description.")
        self.assertEqual(command_help_obj.links[0], {"title": "Azure Test Alpha Docs",
                                                     "url": "https://docs.microsoft.com/azure/test/alpha"})
        self.assertEqual(command_help_obj.links[1], {"url": "https://aka.ms/just-a-long-url"})

        # test that parameters and help are loaded from command function docstring, argument registry help and help.yaml
        obj_param_dict = {param.name: param for param in command_help_obj.parameters}
        param_name_set = {"--arg1 -a", "--arg2 -b", "--arg3", "ARG4"}
        self.assertTrue(set(obj_param_dict.keys()).issuperset(param_name_set))

        self.assertEqual(obj_param_dict["--arg1 -a"].short_summary, "A short summary.")
        self.assertEqual(obj_param_dict["--arg3"].short_summary, "Arg3's docstring help text.")
        self.assertEqual(obj_param_dict["ARG4"].short_summary, "Arg4's summary, yaml. Positional arg, not required.")

        self.assertEqual(obj_param_dict["--arg2 -b"].short_summary, "Arg 2's summary.")
        self.assertEqual(obj_param_dict["--arg2 -b"].long_summary, "A true description of this parameter.")
        self.assertEqual(obj_param_dict["--arg2 -b"].value_sources[0], {"string": "Number range: -5.0 to 5.0"})
        self.assertEqual(obj_param_dict["--arg2 -b"].value_sources[1]['link'], {"url": "https://www.foo.com",
                                                                                "title": "foo"})
        self.assertEqual(obj_param_dict["--arg2 -b"].value_sources[2]['link'], {"command": "az test show",
                                                                                "title": "Show test details"})

        if self.test_cli.cloud.profile in ['2018-03-01-hybrid', 'latest']:
            self.assertEqual(command_help_obj.examples[0].short_summary, "A simple example")
            self.assertEqual(command_help_obj.examples[0].long_summary, "More detail on the simple example.")
            self.assertEqual(command_help_obj.examples[0].command, "az test alpha --arg1 apple --arg2 ball --arg3 cat")
            self.assertEqual(command_help_obj.examples[0].supported_profiles, "2018-03-01-hybrid, latest")
            self.assertEqual(command_help_obj.examples[0].unsupported_profiles, None)

            self.assertEqual(command_help_obj.examples[1].supported_profiles, None)
            self.assertEqual(command_help_obj.examples[1].unsupported_profiles, "2017-03-09-profile")

        if self.test_cli.cloud.profile == '2019-03-01-hybrid':
            self.assertEqual(len(command_help_obj.examples), 1)
            self.assertEqual(command_help_obj.examples[0].short_summary, "Another example unsupported on latest")
            self.assertEqual(command_help_obj.examples[0].command, "az test alpha --arg1 apple --arg2 ball")
            self.assertEqual(command_help_obj.examples[0].unsupported_profiles, '2017-03-09-profile')

        if self.test_cli.cloud.profile == '2017-03-09-profile':
            self.assertEqual(len(command_help_obj.examples), 0)

    @mock.patch('inspect.getmembers', side_effect=mock_inspect_getmembers)
    @mock.patch('pkgutil.iter_modules', side_effect=lambda x: [(None, MOCKED_COMMAND_LOADER_MOD, None)])
    @mock.patch('azure.cli.core.commands._load_command_loader', side_effect=mock_load_command_loader)
    def test_load_from_help_json(self, mocked_load, mocked_pkg_util, mocked_getmembers):
        # setup help.py, help.yaml and help.json
        self.set_help_py()
        path = self.set_help_yaml()  # either (yaml or json) path should work. As both files are in the same temp dir.
        self.set_help_json()
        create_invoker_and_load_cmds_and_args(self.test_cli)

        # mock logic in core._help_loaders for retrieving yaml file from loader path.
        expected_arg = self.test_cli.invocation.commands_loader.cmd_to_loader_map['test alpha'][0].__class__
        with mock.patch('inspect.getfile', side_effect=get_mocked_inspect_getfile(expected_arg, path)):
            group_help_obj = next((help for help in get_all_help(self.test_cli) if help.command == "test"), None)
            command_help_obj = next((help for help in get_all_help(self.test_cli) if help.command == "test alpha"),
                                    None)

            # Test that group and command help are successfully displayed.
            with self.assertRaises(SystemExit):
                self.test_cli.invoke(["test", "-h"])
            with self.assertRaises(SystemExit):
                self.test_cli.invoke(["test", "alpha", "-h"])

        # Test group help
        self.assertIsNotNone(group_help_obj)
        self.assertEqual(group_help_obj.short_summary, "Group json summary.")
        self.assertEqual(group_help_obj.long_summary, "Group json description. A.K.A long description.")
        self.assertEqual(group_help_obj.links[0], {"title": "Azure Json Test Docs",
                                                   "url": "https://docs.microsoft.com/azure/test"})
        self.assertEqual(group_help_obj.links[1], {"url": "https://aka.ms/just-a-url"})

        # Test command help
        self.assertIsNotNone(command_help_obj)
        self.assertEqual(command_help_obj.short_summary, "Command json summary.")
        self.assertEqual(command_help_obj.long_summary, "Command json description. A.K.A long description.")
        self.assertEqual(command_help_obj.links[0], {"title": "Azure Json Test Alpha Docs",
                                                     "url": "https://docs.microsoft.com/azure/test/alpha"})
        self.assertEqual(command_help_obj.links[1], {"url": "https://aka.ms/just-a-long-url"})

        # test that parameters and help are loaded from command function docstring, argument registry help and help.yaml
        obj_param_dict = {param.name: param for param in command_help_obj.parameters}
        param_name_set = {"--arg1 -a", "--arg2 -b", "--arg3", "ARG4"}
        self.assertTrue(set(obj_param_dict.keys()).issuperset(param_name_set))

        self.assertEqual(obj_param_dict["--arg3"].short_summary, "Arg 3's json summary.")
        self.assertEqual(obj_param_dict["--arg3"].long_summary, "A truly true description of this parameter.")
        self.assertEqual(obj_param_dict["--arg3"].value_sources[0], {"string": "Number range: 0 to 10"})
        self.assertEqual(obj_param_dict["--arg3"].value_sources[1]['link'],
                         {"url": "https://www.foo-json.com", "title": "foo-json"})
        self.assertEqual(obj_param_dict["--arg3"].value_sources[2]['link'],
                         {"command": "az test show", "title": "Show test details. Json file"})

        if self.test_cli.cloud.profile in ['2018-03-01-hybrid', 'latest']:
            self.assertEqual(command_help_obj.examples[0].short_summary, "A simple example from json")
            self.assertEqual(command_help_obj.examples[0].long_summary, "More detail on the simple example.")
            self.assertEqual(command_help_obj.examples[0].command, "az test alpha --arg1 alpha --arg2 beta --arg3 chi")
            self.assertEqual(command_help_obj.examples[0].supported_profiles, "2018-03-01-hybrid, latest")

        if self.test_cli.cloud.profile == '2019-03-01-hybrid':
            # only supported example here
            self.assertEqual(len(command_help_obj.examples), 0)

        if self.test_cli.cloud.profile == '2017-03-09-profile':
            self.assertEqual(len(command_help_obj.examples), 0)

        # validate other parameters, which have help from help.py and help.yamls
        self.assertEqual(obj_param_dict["--arg1 -a"].short_summary, "A short summary.")
        self.assertEqual(obj_param_dict["--arg2 -b"].short_summary, "Arg 2's summary.")
        self.assertEqual(obj_param_dict["ARG4"].short_summary, "Arg4's summary, yaml. Positional arg, not required.")
        # arg2's help from help.yaml still preserved.
        self.assertEqual(obj_param_dict["--arg2 -b"].long_summary, "A true description of this parameter.")
        self.assertEqual(obj_param_dict["--arg2 -b"].value_sources[0], {"string": "Number range: -5.0 to 5.0"})
        self.assertEqual(obj_param_dict["--arg2 -b"].value_sources[1]['link'], {"url": "https://www.foo.com",
                                                                                "title": "foo"})
        self.assertEqual(obj_param_dict["--arg2 -b"].value_sources[2]['link'], {"command": "az test show",
                                                                                "title": "Show test details"})

    # create a temporary file in the temp dir. Return the path of the file.
    def _create_new_temp_file(self, data, suffix=""):
        with tempfile.NamedTemporaryFile(mode='w', dir=self._tempdirName, delete=False, suffix=suffix) as f:
            f.write(data)
            return f.name


class TestHelpSupportedProfiles(unittest.TestCase):
    def setUp(self):
        from azure.cli.core.profiles._shared import AZURE_API_PROFILES
        self.test_cli = DummyCli()
        self.all_profiles = AZURE_API_PROFILES
        self.all_profiles_str = " {} ".format(" , ".join(AZURE_API_PROFILES.keys()))

    def test_example_inclusion_basic(self):
        from azure.cli.core._help import CliHelpFile

        cli_ctx = self.test_cli
        cli_ctx.invocation = cli_ctx.invocation_cls(cli_ctx=cli_ctx, commands_loader_cls=cli_ctx.commands_loader_cls,
                                                    parser_cls=cli_ctx.parser_cls, help_cls=cli_ctx.help_cls)
        mock_help_file = CliHelpFile(cli_ctx.invocation.help, "")
        mock_help_file.help_ctx = cli_ctx.invocation.help
        ex_dict = {
            'summary': "Example to test supported-profiles",
            'command': "Az foo bar",
            'supported-profiles': self.all_profiles_str
        }

        # example should be included in all profiles (implicit)
        for profile in self.all_profiles.keys():
            mock_help_file.help_ctx.cli_ctx.cloud.profile = profile
            self.assertTrue(mock_help_file._should_include_example(ex_dict))

        ex_dict.update({
            'supported-profiles': self.all_profiles_str,
            'unsupported-profiles': self.all_profiles_str
        })
        # Assert that an help authoring exception is raised when both types of fields are used.
        with self.assertRaises(HelpAuthoringException):
            mock_help_file._should_include_example(ex_dict)

        del ex_dict['supported-profiles']
        del ex_dict['unsupported-profiles']

    def test_example_supported_profiles(self):
        from azure.cli.core._help import CliHelpFile

        cli_ctx = self.test_cli
        cli_ctx.invocation = cli_ctx.invocation_cls(cli_ctx=cli_ctx,
                                                    commands_loader_cls=cli_ctx.commands_loader_cls,
                                                    parser_cls=cli_ctx.parser_cls, help_cls=cli_ctx.help_cls)
        mock_help_file = CliHelpFile(cli_ctx.invocation.help, "")
        mock_help_file.help_ctx = cli_ctx.invocation.help
        ex_dict = {
            'summary': "Example to test supported-profiles",
            'command': "Az foo bar",
            'supported-profiles': self.all_profiles_str
        }

        # example should be included in all profiles (explicit)
        for profile in self.all_profiles:
            mock_help_file.help_ctx.cli_ctx.cloud.profile = profile
            self.assertTrue(mock_help_file._should_include_example(ex_dict))

        # example should be included in all filtered profiles but not excluded profile
        for excluded_profile in self.all_profiles:
            filtered_profiles = [profile for profile in self.all_profiles if profile != excluded_profile]
            ex_dict['supported-profiles'] = ", ".join(filtered_profiles)

            # excluded profile is not in supported-profiles list and example should be excluded
            mock_help_file.help_ctx.cli_ctx.cloud.profile = excluded_profile
            self.assertFalse(mock_help_file._should_include_example(ex_dict))

            # for other profiles example should show be included.
            for profile in filtered_profiles:
                mock_help_file.help_ctx.cli_ctx.cloud.profile = profile
                self.assertTrue(mock_help_file._should_include_example(ex_dict))

        # example should be included in the sole supported profile
        for sole_profile in self.all_profiles:
            mock_help_file.help_ctx.cli_ctx.cloud.profile = sole_profile

            # try different supported profiles settings in example and handle accordingly
            for profile in self.all_profiles:
                ex_dict['supported-profiles'] = " {} ".format(profile)
                should_include_example = mock_help_file._should_include_example(ex_dict)
                if profile == sole_profile:
                    self.assertTrue(should_include_example)
                else:
                    self.assertFalse(should_include_example)

    def test_example_unsupported_profiles(self):
        from azure.cli.core._help import CliHelpFile

        cli_ctx = self.test_cli
        cli_ctx.invocation = cli_ctx.invocation_cls(cli_ctx=cli_ctx,
                                                    commands_loader_cls=cli_ctx.commands_loader_cls,
                                                    parser_cls=cli_ctx.parser_cls, help_cls=cli_ctx.help_cls)
        mock_help_file = CliHelpFile(cli_ctx.invocation.help, "")
        mock_help_file.help_ctx = cli_ctx.invocation.help
        ex_dict = {
            'summary': "Example to test supported-profiles",
            'command': "Az foo bar",
            'unsupported-profiles': self.all_profiles_str
        }

        # example should be excluded from all profiles (explicit)
        for profile in self.all_profiles:
            mock_help_file.help_ctx.cli_ctx.cloud.profile = profile
            self.assertFalse(mock_help_file._should_include_example(ex_dict))

        # example should be excluded in all filtered profiles
        for included in self.all_profiles:
            filtered_profiles = [profile for profile in self.all_profiles if profile != included]
            ex_dict['unsupported-profiles'] = ", ".join(filtered_profiles)

            # included profile is not in unsupported-profiles list and example should be included
            mock_help_file.help_ctx.cli_ctx.cloud.profile = included
            self.assertTrue(mock_help_file._should_include_example(ex_dict))

            # for other profiles example should show be excluded.
            for profile in filtered_profiles:
                mock_help_file.help_ctx.cli_ctx.cloud.profile = profile
                self.assertFalse(mock_help_file._should_include_example(ex_dict))

        # example should be excluded in the sole unsupported profile
        for sole_profile in self.all_profiles:
            mock_help_file.help_ctx.cli_ctx.cloud.profile = sole_profile

            # try different unsupported profiles settings in example and handle accordingly
            for profile in self.all_profiles:
                ex_dict['unsupported-profiles'] = " {} ".format(profile)
                should_include_example = mock_help_file._should_include_example(ex_dict)
                if profile == sole_profile:
                    self.assertFalse(should_include_example)
                else:
                    self.assertTrue(should_include_example)


if __name__ == '__main__':
    unittest.main()
