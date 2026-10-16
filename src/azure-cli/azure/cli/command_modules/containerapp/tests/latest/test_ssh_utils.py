# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import io
import unittest
from unittest import mock

from azure.cli.command_modules.containerapp import _ssh_utils
from azure.cli.command_modules.containerapp._ssh_utils import (
    _write_to_terminal,
    _decode_and_output_to_terminal,
)

# Lobster emoji (U+1F99E): valid UTF-8, but has no representation in cp1252.
EMOJI = "\U0001f99e"


class _NarrowStdout:
    """Mimics a console whose text codec (e.g. cp1252) cannot encode every
    character. Its ``write`` re-encodes like a real console, so emoji raises
    ``UnicodeEncodeError``; bytes written via the fallback land in ``buffer``."""

    def __init__(self, encoding="cp1252"):
        self.encoding = encoding
        self.buffer = io.BytesIO()

    def write(self, text):
        text.encode(self.encoding)  # raises UnicodeEncodeError on unencodable chars

    def flush(self):
        pass


class SshUtilsTerminalOutputTest(unittest.TestCase):
    def test_write_falls_back_when_char_not_encodable(self):
        text = f"hello {EMOJI} world"
        stdout = _NarrowStdout(encoding="cp1252")

        with mock.patch.object(_ssh_utils.sys, "stdout", stdout):
            _write_to_terminal(text)  # must not raise UnicodeEncodeError

        self.assertEqual(stdout.buffer.getvalue(),
                         text.encode("cp1252", errors="backslashreplace"))

    def test_write_uses_print_fast_path_when_encodable(self):
        stdout = _NarrowStdout(encoding="utf-8")

        with mock.patch.object(_ssh_utils.sys, "stdout", stdout):
            _write_to_terminal("plain ascii")

        # Encodable text goes through print(); the fallback buffer stays empty.
        self.assertEqual(stdout.buffer.getvalue(), b"")

    def test_decode_and_output_handles_emoji_without_disconnecting(self):
        payload = f"openclaw {EMOJI} v1".encode("utf-8")
        response = bytes([_ssh_utils.SSH_PROXY_FORWARD,
                          _ssh_utils.SSH_CLUSTER_STDOUT]) + payload
        connection = mock.MagicMock()
        stdout = _NarrowStdout(encoding="cp1252")

        with mock.patch.object(_ssh_utils.sys, "stdout", stdout):
            _decode_and_output_to_terminal(connection, response, ["utf-8", "latin_1"])

        connection.disconnect.assert_not_called()
        self.assertIn(b"openclaw", stdout.buffer.getvalue())


if __name__ == "__main__":
    unittest.main()
