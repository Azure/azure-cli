# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest


class TestStyle(unittest.TestCase):

    def test_format_styled_text(self):
        from azure.cli.core.style import Style, format_styled_text
        styled_text = [
            (Style.PRIMARY, "Bright White: Primary text color\n"),
            (Style.SECONDARY, "White: Secondary text color\n"),
            (Style.IMPORTANT, "Bright Magenta: Important text color\n"),
            (Style.ACTION, "Bright Blue: Commands, parameters, and system inputs\n"),
            (Style.HYPERLINK, "Bright Cyan: Hyperlink\n"),
            (Style.ERROR, "Bright Red: Error message indicator\n"),
            (Style.SUCCESS, "Bright Green: Success message indicator\n"),
            (Style.WARNING, "Bright Yellow: Warning message indicator\n"),
        ]
        formatted = format_styled_text(styled_text)
        excepted = """\x1b[97mBright White: Primary text color
\x1b[90mWhite: Secondary text color
\x1b[95mBright Magenta: Important text color
\x1b[94mBright Blue: Commands, parameters, and system inputs
\x1b[96mBright Cyan: Hyperlink
\x1b[91mBright Red: Error message indicator
\x1b[92mBright Green: Success message indicator
\x1b[93mBright Yellow: Warning message indicator
\x1b[39m"""
        self.assertEqual(formatted, excepted)

        # Test invalid style
        from azure.cli.core.azclierror import CLIInternalError
        with self.assertRaisesRegex(CLIInternalError, "Invalid style."):
            format_styled_text([("invalid_style", "dummy text",)])

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


if __name__ == '__main__':
    unittest.main()
