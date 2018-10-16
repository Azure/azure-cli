# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from prompt_toolkit.enums import DEFAULT_BUFFER, SEARCH_BUFFER
from prompt_toolkit.filters import Condition, Always, IsDone, HasFocus, RendererHeightIsKnown
from prompt_toolkit.layout.containers import VSplit, HSplit, \
    Window, FloatContainer, Float, ConditionalContainer
from prompt_toolkit.layout.controls import BufferControl, FillControl, TokenListControl
from prompt_toolkit.layout.dimension import LayoutDimension
from prompt_toolkit.layout.lexers import PygmentsLexer, Lexer as PromptLex
from prompt_toolkit.layout.menus import CompletionsMenu
from prompt_toolkit.layout.processors import HighlightSearchProcessor, \
    HighlightSelectionProcessor, \
    ConditionalProcessor, AppendAutoSuggestion
from prompt_toolkit.layout.prompt import DefaultPrompt
from prompt_toolkit.layout.screen import Char

from pygments.token import Token
from pygments.lexer import Lexer as PygLex

from .progress import get_progress_message, get_done

MAX_COMPLETION = 16


# pylint:disable=too-few-public-methods
class LayoutManager(object):
    """ store information and conditions for the layout """

    def __init__(self, shell_ctx):
        self.shell_ctx = shell_ctx

        @Condition
        def show_default(_):
            return self.shell_ctx.is_showing_default

        @Condition
        def show_symbol(_):
            return self.shell_ctx.is_symbols

        @Condition
        def show_progress(_):
            progress = get_progress_message()
            done = get_done()
            return progress != '' and not done

        @Condition
        def has_default_scope(_):
            return self.shell_ctx.default_command == ''

        self.has_default_scope = has_default_scope
        self.show_default = show_default
        self.show_symbol = show_symbol
        self.show_progress = show_progress

        # TODO fix this somehow
        self.input_processors = [
            ConditionalProcessor(
                # By default, only highlight search when the search
                # input has the focus. (Note that this doesn't mean
                # there is no search: the Vi 'n' binding for instance
                # still allows to jump to the next match in
                # navigation mode.)
                HighlightSearchProcessor(preview_search=Always()),
                HasFocus(SEARCH_BUFFER)),
            HighlightSelectionProcessor(),
            ConditionalProcessor(AppendAutoSuggestion(), HasFocus(DEFAULT_BUFFER) & self.has_default_scope)
        ]

    def get_prompt_tokens(self, _):
        """ returns prompt tokens """
        if self.shell_ctx.default_command:
            prompt = 'az {}>> '.format(self.shell_ctx.default_command)
        else:
            prompt = 'az>> '
        return [(Token.Az, prompt)]

    def create_tutorial_layout(self):
        """ layout for example tutorial """
        lexer, _, _ = get_lexers(self.shell_ctx.lexer, None, None)
        layout_full = HSplit([
            FloatContainer(
                Window(
                    BufferControl(
                        input_processors=self.input_processors,
                        lexer=lexer,
                        preview_search=Always()),
                    get_height=get_height),
                [
                    Float(xcursor=True,
                          ycursor=True,
                          content=CompletionsMenu(
                              max_height=MAX_COMPLETION,
                              scroll_offset=1,
                              extra_filter=(HasFocus(DEFAULT_BUFFER))))]),
            ConditionalContainer(
                HSplit([
                    get_hline(),
                    get_param(lexer),
                    get_hline(),
                    Window(
                        content=BufferControl(
                            buffer_name='example_line',
                            lexer=lexer
                        ),
                    ),
                    Window(
                        TokenListControl(
                            get_tutorial_tokens,
                            default_char=Char(' ', Token.Toolbar)),
                        height=LayoutDimension.exact(1)),
                ]),
                filter=~IsDone() & RendererHeightIsKnown()
            )
        ])
        return layout_full

    def create_layout(self, exam_lex, toolbar_lex):
        """ creates the layout """
        lexer, exam_lex, toolbar_lex = get_lexers(self.shell_ctx.lexer, exam_lex, toolbar_lex)

        if not any(isinstance(processor, DefaultPrompt) for processor in self.input_processors):
            self.input_processors.append(DefaultPrompt(self.get_prompt_tokens))

        layout_lower = ConditionalContainer(
            HSplit([
                get_anyhline(self.shell_ctx.config),
                get_descriptions(self.shell_ctx.config, exam_lex, lexer),
                get_examplehline(self.shell_ctx.config),
                get_example(self.shell_ctx.config, exam_lex),

                ConditionalContainer(
                    get_hline(),
                    filter=self.show_default | self.show_symbol
                ),
                ConditionalContainer(
                    Window(
                        content=BufferControl(
                            buffer_name='default_values',
                            lexer=lexer
                        )
                    ),
                    filter=self.show_default
                ),
                ConditionalContainer(
                    get_hline(),
                    filter=self.show_default & self.show_symbol
                ),
                ConditionalContainer(
                    Window(
                        content=BufferControl(
                            buffer_name='symbols',
                            lexer=exam_lex
                        )
                    ),
                    filter=self.show_symbol
                ),
                ConditionalContainer(
                    Window(
                        content=BufferControl(
                            buffer_name='progress',
                            lexer=lexer
                        )
                    ),
                    filter=self.show_progress
                ),
                Window(
                    content=BufferControl(
                        buffer_name='bottom_toolbar',
                        lexer=toolbar_lex
                    ),
                ),
            ]),
            filter=~IsDone() & RendererHeightIsKnown()
        )

        layout_full = HSplit([
            FloatContainer(
                Window(
                    BufferControl(
                        input_processors=self.input_processors,
                        lexer=lexer,
                        preview_search=Always()),
                    get_height=get_height,
                ),
                [
                    Float(xcursor=True,
                          ycursor=True,
                          content=CompletionsMenu(
                              max_height=MAX_COMPLETION,
                              scroll_offset=1,
                              extra_filter=(HasFocus(DEFAULT_BUFFER))))]),
            layout_lower
        ])

        return layout_full


def get_height(cli):
    """ gets the height of the cli """
    if not cli.is_done:
        return LayoutDimension(min=8)
    return None


def get_tutorial_tokens(_):
    """ tutorial tokens """
    return [(Token.Toolbar, 'In Tutorial Mode: Press [Enter] after typing each part')]


def get_lexers(main_lex, exam_lex, tool_lex):
    """ gets all the lexer wrappers """
    if not main_lex:
        return None, None, None
    lexer = None
    if main_lex:
        if issubclass(main_lex, PromptLex):
            lexer = main_lex
        elif issubclass(main_lex, PygLex):
            lexer = PygmentsLexer(main_lex)

    if exam_lex:
        if issubclass(exam_lex, PygLex):
            exam_lex = PygmentsLexer(exam_lex)

    if tool_lex:
        if issubclass(tool_lex, PygLex):
            tool_lex = PygmentsLexer(tool_lex)

    return lexer, exam_lex, tool_lex


def get_anyhline(config):
    """ if there is a line between descriptions and example """
    if config.BOOLEAN_STATES[config.config.get('Layout', 'command_description')] or\
       config.BOOLEAN_STATES[config.config.get('Layout', 'param_description')]:
        return Window(
            width=LayoutDimension.exact(1),
            height=LayoutDimension.exact(1),
            content=FillControl('-', token=Token.Line))
    return get_empty()


def get_descript(lexer):
    """ command description window """
    return Window(
        content=BufferControl(
            buffer_name="description",
            lexer=lexer))


def get_param(lexer):
    """ parameter description window """
    return Window(
        content=BufferControl(
            buffer_name="parameter",
            lexer=lexer))


def get_example(config, exam_lex):
    """ example description window """
    if config.BOOLEAN_STATES[config.config.get('Layout', 'examples')]:
        return Window(
            content=BufferControl(
                buffer_name="examples",
                lexer=exam_lex))
    return get_empty()


def get_examplehline(config):
    """ gets a line if there are examples """
    if config.BOOLEAN_STATES[config.config.get('Layout', 'examples')]:
        return get_hline()
    return get_empty()


def get_empty():
    """ returns an empty window because of syntaxical issues """
    return Window(
        content=FillControl(' ')
    )


def get_hline():
    """ gets a horiztonal line """
    return Window(
        width=LayoutDimension.exact(1),
        height=LayoutDimension.exact(1),
        content=FillControl('-', token=Token.Line))


def get_vline():
    """ gets a vertical line """
    return Window(
        width=LayoutDimension.exact(1),
        height=LayoutDimension.exact(1),
        content=FillControl('*', token=Token.Line))


def get_descriptions(config, exam_lex, lexer):
    """ based on the configuration settings determines which windows to include """
    if config.BOOLEAN_STATES[config.config.get('Layout', 'command_description')]:
        if config.BOOLEAN_STATES[config.config.get('Layout', 'param_description')]:
            return VSplit([
                get_descript(exam_lex),
                get_vline(),
                get_param(lexer),
            ])
        return get_descript(exam_lex)
    elif config.BOOLEAN_STATES[config.config.get('Layout', 'param_description')]:
        return get_param(lexer)
    return get_empty()
