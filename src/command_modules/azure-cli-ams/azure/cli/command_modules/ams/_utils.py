# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from datetime import datetime, timedelta

import uuid
import re
import isodate


def _gen_guid():
    return uuid.uuid4()


def _is_guid(guid):
    try:
        uuid.UUID(guid)
        return True
    except ValueError:
        pass
    return False


def parse_iso_duration(str_duration):
    iso_duration_format_value = None
    if str_duration:
        datetime_duration = datetime.strptime(str_duration, '%H:%M:%S')
        iso_duration_format_value = isodate.duration_isoformat(timedelta(hours=datetime_duration.hour,
                                                                         minutes=datetime_duration.minute,
                                                                         seconds=datetime_duration.second))
    return iso_duration_format_value


def camel_to_snake(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
