# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Internal class for query execution context implementation in the Azure Configuration service.
"""

from collections import deque


class QueryExecutionContext(object):
    """
    This is the execution context class.
    """

    def __init__(self, client, options, fetch_function):
        """
        Constructor

        :param AzconfigClient client:
        :param dict options:
            The request options for the request.
        :param method fetch_function
        """
        self._client = client
        self._options = options
        self._fetch_function = fetch_function
        self._continuation = None
        self._has_started = False
        self._buffer = deque()

    def _has_more_pages(self):
        return not self._has_started or self._continuation

    def fetch_next_block(self):
        """Returns a block of results with respecting retry policy.

        This method only exists for backward compatibility reasons. (Because KeyValueIterable
        has exposed fetch_next_block api).

        :return:
            List of results.
        :rtype: list
        """
        if not self._has_more_pages():
            return []

        if self._buffer:
            # if there is anything in the buffer returns that
            res = list(self._buffer)
            self._buffer.clear()
            return res

        # fetches the next block
        while self._has_more_pages() and not self._buffer:
            return self._fetch_items(self._fetch_function)

    def __iter__(self):
        """Returns itself as an iterator"""
        return self

    def __next__(self):
        """Returns the next query result.

        :return:
            The next query result.
        :rtype: dict
        :raises StopIteration: If no more result is left.
        """
        if not self._buffer:
            results = self.fetch_next_block()
            if not results:
                raise StopIteration
            self._buffer.extend(results)

        return self._buffer.popleft()

    def _fetch_items(self, fetch_function):
        """Fetches more items

        :param method fetch_function

        :return:
            List of fetched items.
        :rtype: list
        """
        fetched_items = []

        if self._continuation or not self._has_started:
            if not self._has_started:
                self._has_started = True

            fetched_items, self._continuation = fetch_function(
                self._options, self._continuation)

        return fetched_items

    next = __next__  # Python 2 compatibility.
