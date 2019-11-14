# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from datetime import datetime, timedelta

import uuid
import re
import json
import isodate

from knack.log import get_logger
logger = get_logger(__name__)

iso8601pattern = re.compile("^P(?!$)(\\d+Y)?(\\d+M)?(\\d+W)?(\\d+D)?(T(?=\\d)(\\d+H)?(\\d+M)?(\\d+.)?(\\d+S)?)?$")


def _gen_guid():
    return uuid.uuid4()


def _is_guid(guid):
    try:
        uuid.UUID(guid)
        return True
    except ValueError:
        pass
    return False


def parse_duration(str_duration):
    if str_duration:
        if iso8601pattern.match(str_duration):
            return isodate.parse_duration(str_duration)

        return parse_timedelta(str_duration)
    return None


def parse_timedelta(str_duration):
    if str_duration:
        datetime_duration = datetime.strptime(str_duration, '%H:%M:%S')
    return timedelta(hours=datetime_duration.hour or 0,
                     minutes=datetime_duration.minute or 0,
                     seconds=datetime_duration.second or 0)


def camel_to_snake(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def snake_to_camel_case(snake_str):
    components = snake_str.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])


class JsonBytearrayEncoder(json.JSONEncoder):
    DATE_FORMAT = "%Y-%m-%d"
    TIME_FORMAT = "%H:%M:%S"

    def default(self, obj):  # pylint: disable=E0202,W0221
        if isinstance(obj, datetime):
            return obj.strftime("%s %s" % (self.DATE_FORMAT, self.TIME_FORMAT))

        if isinstance(obj, bytearray):
            return bytes(obj).decode('utf-8', 'ignore')

        try:
            return obj.toJSON()
        except Exception:  # pylint: disable=W0703
            obj = vars(obj)
            obj.pop('additional_properties', None)
            keys = list(obj.keys())
            for key in keys:
                obj[snake_to_camel_case(key)] = obj.pop(key)
            return obj


def create_ip_range(resource_name, ip):
    from azure.mgmt.media.models import IPRange
    subnet_prefix_length = None
    try:
        if '/' in ip:
            ipSplit = ip.split('/')
            ip = ipSplit[0]
            subnet_prefix_length = ipSplit[1]
    except ValueError:
        pass
    return IPRange(name=("{}_{}".format(resource_name, ip)), address=ip, subnet_prefix_length=subnet_prefix_length)


# The Media Services SDK does not throw an exception for 404s.
# This helper will make our 'not founds' look like other services.
def show_resource_not_found_message(group, account, ams_type, name):
    import sys
    message = build_resource_not_found_message(group, account, ams_type, name)
    from azure.cli.core.azlogging import CommandLoggerContext
    with CommandLoggerContext(logger):
        logger.error(message)
        sys.exit(3)


def build_resource_not_found_message(group, account, ams_type, name):
    message = "The Resource 'Microsoft.Media/mediaServices/{}/{}/{}' under resource group '{}' was not found." \
        .format(account, ams_type, name, group)
    return message


def show_child_resource_not_found_message(group, account, ams_type, name, ams_child_type, child_name):
    import sys
    message = build_child_resource_not_found_message(account, ams_type, name, ams_child_type, child_name, group)
    from azure.cli.core.azlogging import CommandLoggerContext
    with CommandLoggerContext(logger):
        logger.error(message)
        sys.exit(3)


def build_child_resource_not_found_message(group, account, ams_type, name, ams_child_type, child_name):
    message = "The Resource 'Microsoft.Media/mediaServices/{}/{}/{}/{}/{}' under resource group '{}' was not found." \
        .format(account, ams_type, name, ams_child_type, child_name, group)
    return message
