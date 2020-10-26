# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.log import get_logger

logger = get_logger(__name__)


def list_queues(client, include_metadata=False, marker=None, num_results=None,
                prefix=None, show_next_marker=None, **kwargs):
    from ..track2_util import list_generator
    generator = client.list_queues(name_starts_with=prefix, include_metadata=include_metadata,
                                   results_per_page=num_results, **kwargs)
    pages = generator.by_page(continuation_token=marker)
    result = list_generator(pages=pages, num_results=num_results)

    if show_next_marker:
        next_marker = {"nextMarker": pages.continuation_token}
        result.append(next_marker)
    else:
        if pages.continuation_token:
            logger.warning('Next Marker:')
            logger.warning(pages.continuation_token)

    return result
