# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import sys
import unittest
from unittest import mock

from azure.cli.core.style import Style, Theme, format_styled_text, print_styled_text, _is_modern_terminal


class TestStyle(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        try:
            # Clear `theme` attribute that may be set by other tests.
            delattr(format_styled_text, 'theme')
        except AttributeError:
            pass

    def test_format_styled_text(self):
        # Test list input
        styled_text = [
            (Style.PRIMARY, "White: Primary text color\n"),
            (Style.SECONDARY, "Bright Black: Secondary text color\n"),
            (Style.IMPORTANT, "Bright Magenta: Important text color\n"),
            (Style.ACTION, "Bright Blue: Commands, parameters, and system inputs\n"),
            (Style.HYPERLINK, "Bright Cyan: Hyperlink\n"),
            (Style.ERROR, "Bright Red: Error message indicator\n"),
            (Style.SUCCESS, "Bright Green: Success message indicator\n"),
            (Style.WARNING, "Bright Yellow: Warning message indicator\n"),
        ]
        formatted = format_styled_text(styled_text)
        excepted = """\x1b[39mWhite: Primary text color
\x1b[90mBright Black: Secondary text color
\x1b[95mBright Magenta: Important text color
\x1b[94mBright Blue: Commands, parameters, and system inputs
\x1b[96mBright Cyan: Hyperlink
\x1b[91mBright Red: Error message indicator
\x1b[92mBright Green: Success message indicator
\x1b[93mBright Yellow: Warning message indicator
\x1b[39m"""
        self.assertEqual(formatted, excepted)

        # Test str input
        styled_text = "Primary text color"
        formatted = format_styled_text(styled_text)
        excepted = "\x1b[39mPrimary text color\x1b[39m"
        self.assertEqual(formatted, excepted)

        # Test tuple input
        styled_text = (Style.PRIMARY, "Primary text color")
        formatted = format_styled_text(styled_text)
        excepted = "\x1b[39mPrimary text color\x1b[39m"
        self.assertEqual(formatted, excepted)

    def test_format_styled_text_on_error(self):
        # Test invalid style
        from azure.cli.core.azclierror import CLIInternalError
        with self.assertRaisesRegex(CLIInternalError, "Invalid style."):
            format_styled_text([("invalid_style", "dummy text")])

        # Test invalid styled style
        with self.assertRaisesRegex(CLIInternalError, "Invalid styled text."):
            format_styled_text([(Style.PRIMARY,)])
        with self.assertRaisesRegex(CLIInternalError, "Invalid styled text."):
            format_styled_text(["dummy text"])

    def test_highlight_command(self):
        from azure.cli.core.style import Style, highlight_command, format_styled_text

        raw_commands = [
            'az cmd',
            'az cmd sub-cmd',
            'az cmd --arg val',
            'az cmd --arg=val',
            'az cmd --arg "content with space"',
            'az cmd --arg val1 val2',
            'az cmd sub-cmd --arg1 val1 --arg2=" " --arg3 "val2 val3" --arg4 val4'
        ]

        expected = [
            [(Style.ACTION, 'az'), (Style.ACTION, ' cmd')],
            [(Style.ACTION, 'az'), (Style.ACTION, ' cmd'), (Style.ACTION, ' sub-cmd')],
            [(Style.ACTION, 'az'), (Style.ACTION, ' cmd'), (Style.ACTION, ' --arg'), (Style.PRIMARY, ' val')],
            [(Style.ACTION, 'az'), (Style.ACTION, ' cmd'), (Style.PRIMARY, ' --arg=val')],
            [(Style.ACTION, 'az'), (Style.ACTION, ' cmd'), (Style.ACTION, ' --arg'), (Style.PRIMARY, ' "content'),
             (Style.PRIMARY, ' with'), (Style.PRIMARY, ' space"')],
            [(Style.ACTION, 'az'), (Style.ACTION, ' cmd'), (Style.ACTION, ' --arg'),
             (Style.PRIMARY, ' val1'), (Style.PRIMARY, ' val2')],
            [(Style.ACTION, 'az'), (Style.ACTION, ' cmd'), (Style.ACTION, ' sub-cmd'), (Style.ACTION, ' --arg1'),
             (Style.PRIMARY, ' val1'), (Style.PRIMARY, ' --arg2="'), (Style.PRIMARY, ' "'), (Style.ACTION, ' --arg3'),
             (Style.PRIMARY, ' "val2'), (Style.PRIMARY, ' val3"'), (Style.ACTION, ' --arg4'), (Style.PRIMARY, ' val4')]
        ]

        for cmd_index, command in enumerate(raw_commands):
            styled_command = highlight_command(command)
            expected_style = expected[cmd_index]

            for tpl_index, style_tuple in enumerate(styled_command):
                expected_tuple = expected_style[tpl_index]
                self.assertEqual(style_tuple[0], expected_tuple[0])
                self.assertEqual(style_tuple[1], expected_tuple[1])

    def test_format_styled_text_theme(self):
        from azure.cli.core.style import Style, format_styled_text
        styled_text = [
            (Style.PRIMARY, "White: Primary text color\n"),
            (Style.SECONDARY, "Bright Black: Secondary text color\n"),
        ]
        formatted = format_styled_text(styled_text)
        excepted = """\x1b[39mWhite: Primary text color
\x1b[90mBright Black: Secondary text color
\x1b[39m"""
        self.assertEqual(formatted, excepted)

        # Color is turned off via param
        formatted = format_styled_text(styled_text, theme='none')
        excepted_plaintext = ("White: Primary text color\n"
                              "Bright Black: Secondary text color\n")
        self.assertEqual(formatted, excepted_plaintext)

        # Color is turned off via function attribute
        format_styled_text.theme = 'none'
        formatted = format_styled_text(styled_text)
        self.assertEqual(formatted, excepted_plaintext)

        # Function attribute is overridden by param
        format_styled_text.theme = 'dark'
        formatted = format_styled_text(styled_text, theme='none')
        self.assertEqual(formatted, excepted_plaintext)

        # Specify theme with Enum
        formatted = format_styled_text(styled_text, theme=Theme.NONE)
        self.assertEqual(formatted, excepted_plaintext)

        delattr(format_styled_text, "theme")

    @mock.patch("builtins.print")
    @mock.patch("azure.cli.core.style.format_styled_text")
    def test_print_styled_text(self, mock_format_styled_text, mock_print):
        # Just return the original input
        mock_format_styled_text.side_effect = lambda obj: obj

        # Default to stderr
        print_styled_text("test text")
        mock_print.assert_called_with("test text", file=sys.stderr)

        # No args
        print_styled_text()
        mock_print.assert_called_with(file=sys.stderr)

        # Multiple args
        print_styled_text("test text 1", "test text 2")
        mock_print.assert_called_with("test text 1", "test text 2", file=sys.stderr)


class TestUtils(unittest.TestCase):

    def test_is_modern_terminal(self):
        with mock.patch.dict("os.environ", clear=True):
            self.assertEqual(_is_modern_terminal(), False)
        with mock.patch.dict("os.environ", WT_SESSION='c25cb945-246a-49e5-b37a-1e4b6671b916'):
            self.assertEqual(_is_modern_terminal(), True)
        with mock.patch.dict("os.environ", TERM_PROGRAM='vscode'):
            self.assertEqual(_is_modern_terminal(), True)


if __name__ == '__main__':
    unittest.main()
