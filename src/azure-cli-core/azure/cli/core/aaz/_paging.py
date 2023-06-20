# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import base64
import itertools
import json

from azure.cli.core.aaz import AAZUndefined, has_value


class AAZPageIterator:
    def __init__(self, executor, extract_result, cli_ctx, next_link, offset, page_size):
        self._executor = executor
        self._extract_result = extract_result
        self._cli_ctx = cli_ctx
        self._next_link = next_link
        self._did_once_already = False if next_link is None else True  # desired start
        self._total = page_size + offset if has_value(page_size) else None
        self._start = offset
        self._curr_link = None
        self._page_size = None

    def __iter__(self):
        return self

    def __next__(self):
        def next_token(_, result):
            from knack.log import get_logger
            logger = get_logger(__name__)
            logger.warning(f"Token of next page: {base64.b64encode(token).decode('utf-8')}")

        if self._total is not None and self._total < 0:
            from knack.events import EVENT_CLI_SUCCESSFUL_EXECUTE
            token = {"next_link": self._curr_link, "offset": self._page_size + self._total}
            token = json.dumps(token).encode("utf-8")
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
        self._page_size = len(curr_page)
        self._total -= self._page_size

        if self._total < 0:
            return iter(curr_page[start:self._total])  # smaller than current page

        return iter(curr_page[start:])


class AAZPaged:
    def __init__(self, executor, extract_result, cli_ctx, next_token=AAZUndefined, page_size=AAZUndefined):
        if has_value(page_size) and has_value(next_token):
            next_token = json.loads(next_token)
        else:
            next_token = {"next_link": None, "offset": 0}  # default value

        self._page_iterator = itertools.chain.from_iterable(
            AAZPageIterator(
                executor=executor,
                extract_result=extract_result,
                cli_ctx=cli_ctx,
                next_link=next_token["next_link"],
                offset=next_token["offset"],
                page_size=page_size
            )
        )

    def __repr__(self):
        return "<iterator object azure.cli.core.aaz.paging.AAZPaged at {}>".format(hex(id(self)))

    def __iter__(self):
        return self

    def __next__(self):
        return next(self._page_iterator)
