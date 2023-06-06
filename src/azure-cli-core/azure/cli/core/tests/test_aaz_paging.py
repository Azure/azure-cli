# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest


class TestAAZPaging(unittest.TestCase):

    def test_aaz_paging_sample(self):
        from azure.cli.core.aaz._paging import AAZPaged
        from azure.cli.core.aaz import AAZUndefined
        data_by_pages = [(['a', 'b', 'c'], 1), (['d', 'e'], 2), (['f'], 3), (['g', 'h'], AAZUndefined)]
        result = {
            "value": AAZUndefined,
            "next_link": AAZUndefined,
        }

        def executor(next_link):
            if next_link is None:
                next_link = 0
            value, next_link = data_by_pages[next_link]
            result["value"] = value
            result['next_link'] = next_link

        def extract_result():
            return result['value'], result['next_link']

        paged = AAZPaged(executor=executor, extract_result=extract_result)
        self.assertTrue(list(paged) == ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'])
