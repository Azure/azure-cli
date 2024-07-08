# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from azure.cli.core.aaz import AAZUndefined
from azure.cli.core.aaz._paging import AAZPaged, AAZPageIterator
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
            executor=executor, extract_result=extract_result, cli_ctx=DummyCli(),
            token=next_token, limit=4
        )
        self.assertTrue(list(paged) == ["e", "f", "g", "h"])

    def test_aaz_paging_iterator(self):
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

        page_iterator = AAZPageIterator(
            executor=executor, extract_result=extract_result, cli_ctx=DummyCli(),
            next_link=1, offset=1, limit=4
        )

        # | a b c | d e | f | g h |
        #           *
        self.assertTrue(page_iterator._next_link == 1)
        self.assertTrue(page_iterator._start == 1)  # offset
        self.assertTrue(page_iterator._total == 5)
        # | a b c | d e | f | g h |
        #                 *
        next(page_iterator)
        self.assertTrue(page_iterator._next_link == 2)
        self.assertTrue(page_iterator._total == 3)
        # | a b c | d e | f | g h |
        #                     *
        next(page_iterator)
        self.assertTrue(page_iterator._next_link == 3)
        self.assertTrue(page_iterator._total == 2)
        # | a b c | d e | f | g h |
        #                          *
        next(page_iterator)
        self.assertTrue(page_iterator._next_link == AAZUndefined)
        self.assertTrue(page_iterator._total == 0)
