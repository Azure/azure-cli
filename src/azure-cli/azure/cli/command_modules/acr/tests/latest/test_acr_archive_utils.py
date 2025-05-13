# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import re
import unittest

from azure.cli.command_modules.acr._archive_utils import IgnoreRule

class AcrArchiveUtilsTests(unittest.TestCase):
    def test_ignore_rule(self):
        test_data = (
            ("**/bin", "folder1/folder2/folder3/bin", True),
            ("**/bin", "user/roundrobin", False),
            ("**/bin", "user/bin/hello", False),
            ("**/bin", "bin", False),
            ("**/bin", "user/bin", True),
            ("**//bin", "user/roundrobin", False),
            ("**/bin/**", "bin", False),
            ("**/bin/**", "user/bin", False),
            ("**/bin/**", "user/bin/hello", True),            
            ("**/bin/**", "user1/user2/bin/user3/user4", True),
            ("**/bin/**", "user/bin/roundroubin", True),
            ("**/bin/**", "user/roundroubin/bin", False),
            ("**/bin/**/bin", "bin", False),
            ("**/bin/**/bin", "user/roundroubin/abc/bin", False),
            ("**/bin/**/bin", "user/bin/roundroubin/roundroubin", False),
            ("**/bin/**/bin", "user/bin/abc/bin", True),
            ("**/bin/**/bin", "user/bin/roundroubin/bin/file", False),
            ("abc", "abc", True),
            ("*", "abc", True),
            ("*c", "abc", True),
            ("a*", "a", True),
            ("a*", "abc", True),
            ("a*", "ab/c", False),
            ("a*/b", "abc/b", True),
            ("a*/b", "a/c/b", False),
            ("a*b*c*d*e*/f", "axbxcxdxe/f", True),
            ("a*b*c*d*e*/f", "axbxcxdxexxx/f", True),
            ("a*b*c*d*e*/f", "axbxcxdxe/xxx/f", False),
            ("a*b*c*d*e*/f", "axbxcxdxexxx/fff", False),
            ("a*b?c*x", "abxbbxdbxebxczzx", True),
            ("a*b?c*x", "abxbbxdbxebxczzy", False),
            ("a?b", "a☺b", True),
            ("a?b", "a/b", False),
            ("a*b", "a/b", False),
            ("*x", "xxx", True),
        )
        for rule, value, expected in test_data:
            with self.subTest(expected=expected, value=value, rule=rule):
                item = IgnoreRule(rule=rule)
                matched = bool(re.match(item.pattern, value))
                self.assertEqual(expected, matched)
