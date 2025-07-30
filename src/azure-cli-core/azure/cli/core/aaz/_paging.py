# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import base64
import itertools
import json


class AAZPageIterator:  # pylint: disable=too-many-instance-attributes
    def __init__(self, executor, extract_result, cli_ctx, next_link, offset, limit):
        self._executor = executor
        self._extract_result = extract_result
        self._cli_ctx = cli_ctx
        self._next_link = next_link
        self._did_once_already = bool(next_link)  # desired start
        self._total = limit + offset if isinstance(limit, int) else None
        self._start = offset
        self._curr_link = None
        self._curr_size = None

    def __iter__(self):
        return self

    def __next__(self):
        def next_token(_, result):  # pylint: disable=unused-argument
            from knack.log import get_logger
            logger = get_logger(__name__)

            token = {"next_link": self._curr_link, "offset": self._curr_size + self._total}
            token = json.dumps(token).encode("utf-8")
            logger.warning("Token of next page: %s", base64.b64encode(token).decode("utf-8"))

        if self._total is not None and self._total < 0:
            from knack.events import EVENT_CLI_SUCCESSFUL_EXECUTE
            self._cli_ctx.register_event(EVENT_CLI_SUCCESSFUL_EXECUTE, next_token)

            raise StopIteration

        if not self._next_link and self._did_once_already:
            raise StopIteration("End of paginating.")

        self._executor(self._next_link)
        self._did_once_already = True
        self._curr_link = self._next_link
        curr_page, self._next_link = self._extract_result()

        if self._total is None:
            return iter(curr_page)

        start = self._start  # record 1st time only
        self._start = 0
        self._curr_size = len(curr_page)
        self._total -= self._curr_size

        if self._total < 0:
            return iter(curr_page[start:self._total])  # smaller than current page

        return iter(curr_page[start:])


class AAZPaged:
    def __init__(self, executor, extract_result, cli_ctx, token=None, limit=None):
        if isinstance(limit, int) and isinstance(token, str):
            next_token = json.loads(token)
        else:
            next_token = {"next_link": None, "offset": 0}  # default value

        self._page_iterator = itertools.chain.from_iterable(
            AAZPageIterator(
                executor=executor,
                extract_result=extract_result,
                cli_ctx=cli_ctx,
                next_link=next_token["next_link"],
                offset=next_token["offset"],
                limit=limit
            )
        )

    def __repr__(self):
        return "<iterator object azure.cli.core.aaz.paging.AAZPaged at {}>".format(hex(id(self)))

    def __iter__(self):
        return self

    def __next__(self):
        return next(self._page_iterator)
