# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import azure.cli.command_modules.appconfig._azconfig.execution_context as execution_context

# pylint: disable=too-few-public-methods


class KeyValueIterable(object):
    """Represents an iterable object of the query results."""

    def __init__(self, client, query_options, fetch_function):
        """
        Instantiates a KeyValueIterable for queries.

        :param DocumentClient client:
            Instance of Azconfig client.
        :param QueryKeyValueCollectionOptions query_options:
            The query options for the request.
        :param method fetch_function:
        """

        self._client = client
        self.query_options = query_options
        self.fetch_function = fetch_function
        self._ex_context = None

    def __iter__(self):
        """Makes this class iterable.
        """
        return self.Iterator(self)

    class Iterator(object):
        def __init__(self, iterable):
            self._iterable = iterable
            self._finished = False
            self._ex_context = execution_context.QueryExecutionContext(
                self._iterable, self._iterable.query_options, self._iterable.fetch_function)

        def __iter__(self):
            # Always returns self
            return self

        # Support Python 3.x iteration
        def __next__(self):
            return next(self._ex_context)

        # Support Python 2.x iteration
        def next(self):
            return self.__next__()

    def fetch_next_block(self):
        """Returns a block of results.

        This method only exists for backward compatibility reasons. (Because KeyValueIterable
        has exposed fetch_next_block api).

        :return:
            List of results.
        :rtype:
            list
        """
        if self._ex_context is None:
            # initiates execution context for the first time
            self._ex_context = execution_context.QueryExecutionContext(
                self, self.query_options, self.fetch_function)

        return self._ex_context.fetch_next_block()
