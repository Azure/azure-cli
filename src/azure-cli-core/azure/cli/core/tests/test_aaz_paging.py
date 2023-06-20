# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from azure.cli.core.aaz import AAZUndefined
from azure.cli.core.aaz._paging import AAZPaged
from azure.cli.core.mock import DummyCli


class TestAAZPaging(unittest.TestCase):

    def test_aaz_paging_sample(self):
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

        paged = AAZPaged(executor=executor, extract_result=extract_result, cli_ctx=DummyCli())
        self.assertTrue(list(paged) == ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'])

    def test_aaz_paging_with_limit_and_token(self):
        data_by_pages = [
            (["a", "b", "c"], 1),
            (["d", "e"], 2),
            (["f"], 3),
            (["g", "h"], AAZUndefined)
        ]
        result = {
            "value": AAZUndefined,
            "next_link": AAZUndefined
        }

        def executor(next_link):
            if next_link is None:
                next_link = 0
            value, next_link = data_by_pages[next_link]
            result["value"] = value
            result["next_link"] = next_link

        def extract_result():
            return result["value"], result["next_link"]

        next_token = '{"next_link": 1, "offset": 1}'
        paged = AAZPaged(
            executor=executor, extract_result=extract_result, cli_ctx=DummyCli(), next_token=next_token, page_size=3
        )
        self.assertTrue(list(paged) == ["e", "f", "g"])

        next_token = '{"next_link": 2, "offset": 1}'
        paged = AAZPaged(
            executor=executor, extract_result=extract_result, cli_ctx=DummyCli(), next_token=next_token, page_size=4
        )
        self.assertTrue(list(paged) == ["g", "h"])
