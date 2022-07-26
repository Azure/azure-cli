# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import argparse
from knack.util import CLIError
from azure.mgmt.eventgrid.models import (
    InlineEventProperties
)

DESCRIPTION = "description"
DOCUMENTATION_URL = "documentation-url"
DATA_SCHEMA_URL = "data-schema-url"


# pylint: disable=protected-access
# pylint: disable=too-few-public-methods
class AddInlineEventType(argparse._AppendAction):
    def __call__(self, parser, namespace, values, option_string=None):
        valuesLen = len(values)
        usage_error_msg = ("usage error: --inline-event-type KEY [description=<description>] "
                           "[documentation-url=<url>] [data-schema-url=<url>]")
        if valuesLen < 1 or valuesLen > 4:
            raise CLIError(usage_error_msg)

        # First positional argument is the key
        event_type_key = values[0]
        values.pop(0)

        description = None
        documentation_url = None
        data_schema_url = None
        for item in values:
            try:
                key, value = item.split('=', 1)
                if key.lower() == DESCRIPTION:
                    description = value
                elif key.lower() == DOCUMENTATION_URL:
                    documentation_url = value
                elif key.lower() == DATA_SCHEMA_URL:
                    data_schema_url = value
                else:
                    raise ValueError()
            except ValueError:
                raise CLIError(usage_error_msg)

        inline_event_props = InlineEventProperties(
            description=description,
            documentation_url=documentation_url,
            data_schema_url=data_schema_url)

        if namespace.inline_event_type is None:
            namespace.inline_event_type = {}
        namespace.inline_event_type[event_type_key] = inline_event_props
