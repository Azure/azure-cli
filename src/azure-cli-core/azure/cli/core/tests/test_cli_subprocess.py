# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import subprocess
import unittest
import platform
from azure.cli.core import cli_subprocess


class TestCliSubprocess(unittest.TestCase):

    def test_cli_subprocess_run(self):
        cmd = ["echo", "abc"]
        if platform.system().lower() == "windows":
            cmd = ["cmd.exe", "/c"] + cmd
        output = cli_subprocess.run(cmd, stdout=subprocess.PIPE)
        self.assertEqual(output.returncode, 0, "error when run cmd in shell")
        self.assertEqual(output.stdout.decode("utf8").strip(), "abc", "unexpected output when run cmd")

    def test_cli_subprocess_popen(self):
        cmd = ["echo", "abc"]
        if platform.system().lower() == "windows":
            cmd = ["cmd.exe", "/c"] + cmd
        process = cli_subprocess.CliPopen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, _ = process.communicate()
        self.assertEqual(stdout.decode("utf8").strip(), "abc", "unexpected output when run cmd in popen")

    def test_cli_subprocess_check_output(self):
        cmd = ["echo", "abc"]
        if platform.system().lower() == "windows":
            cmd = ["cmd.exe", "/c"] + cmd
        output = cli_subprocess.check_output(cmd, stderr=subprocess.PIPE)
        self.assertEqual(output.decode("utf8").strip(), "abc", "unexpected output when run cmd in check output")

    def test_cli_subprocess_call(self):
        cmd = ["echo", "abc"]
        if platform.system().lower() == "windows":
            cmd = ["cmd.exe", "/c"] + cmd
        output = cli_subprocess.call(cmd)
        self.assertEqual(int(output), 0, "unexpected output when run cmd in call")

    def test_cli_subprocess_shell(self):
        cmd = ["echo", "ab;echo 123"]
        if platform.system().lower() == "windows":
            cmd = ["cmd.exe", "/c"] + cmd
        process = cli_subprocess.CliPopen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True,
                                          enable_arg_mask=True)
        stdout, _ = process.communicate()
        self.assertEqual(stdout.decode("utf8").strip(), "abecho123", "unexpected output when run cmd in popen")

    def test_cli_subprocess_arg_type_check(self):
        cmd = "echo abc"
        if platform.system().lower() == "windows":
            cmd = "cmd.exe /c " + cmd
        from azure.cli.core.azclierror import ArgumentUsageError
        with self.assertRaises(ArgumentUsageError):
            cli_subprocess.CliPopen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)

    def test_subprocess_shell(self):
        if platform.system().lower() == "windows":
            return
        cmd = "echo ab;echo 123"
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        stdout, _ = process.communicate()
        self.assertEqual(stdout.decode("utf8").strip(), "ab\n123", "unexpected output when run cmd in popen")


if __name__ == '__main__':
    unittest.main()
