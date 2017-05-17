# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from pygments.lexer import RegexLexer, words
from pygments.token import Name, Keyword, Operator, Text, Number

from azclishell.gather_commands import GatherCommands


class AzLexer(RegexLexer):
    """
    A custom lexer for Azure CLI
    """

    commands = GatherCommands()
    tokens = {
        'root': [
            (words(
                tuple(kid.data for kid in commands.command_tree.children),
                prefix=r'\b',
                suffix=r'\b'),
             Keyword),  # top level commands
            (words(
                tuple(commands.get_all_subcommands()),
                prefix=r'\b',
                suffix=r'\b'),
             Keyword.Declaration),  # all other commands
            (words(
                tuple(param for param in commands.completable_param + commands.global_param),
                prefix=r'',
                suffix=r'\b'),
             Name.Class),  # parameters
            (r'.', Text),  # all else
            (r' .', Text),
        ]
    }


class ExampleLexer(RegexLexer):
    """ Lexer for the example description """
    tokens = {
        'root': [
            (r' .', Number),
            (r'.', Number),
        ]
    }


class ToolbarLexer(RegexLexer):
    """ Lexer for the the toolbar """
    tokens = {
        'root': [
            (r' .', Operator),
            (r'.', Operator),
        ]
    }
