# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import itertools
from typing import Iterator, TypeVar
import logging

_LOGGER = logging.getLogger(__name__)

ReturnType = TypeVar("ReturnType")


class AAZPageIterator(Iterator[Iterator[ReturnType]]):
    def __init__(self, executor, extract_result):
        self._executor = executor
        self._extract_result = extract_result
        self._next_link = None
        self._did_once_already = False

    def __iter__(self):
        return self

    def __next__(self):
        if not self._next_link and self._did_once_already:
            raise StopIteration("End of paging")
        self._executor(self._next_link)
        self._did_once_already = True
        result, self._next_link = self._extract_result()
        return iter(result)


class AAZPaged(Iterator[ReturnType]):

    def __init__(self, executor, extract_result):
        self._page_iterator = itertools.chain.from_iterable(
            AAZPageIterator(
                executor=executor,
                extract_result=extract_result
            )
        )

    def __repr__(self):
        return "<iterator object azure.cli.core.aaz.paging.AAZPaged at {}>".format(hex(id(self)))

    def __iter__(self):
        return self

    def __next__(self):
        return next(self._page_iterator)
