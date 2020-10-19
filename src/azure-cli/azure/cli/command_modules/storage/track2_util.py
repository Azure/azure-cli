# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def _dont_fail_on_exist(ex, error_code):
    """
    don't throw exception if the resource doesn't exist.
    This is called by create_* APIs with fail_on_exist=False
    :param error:
    :param resource:
    :return:
    """
    if ex.error_code == error_code:
        return False
    raise ex


def _if_match(if_match, **kwargs):
    from azure.core import MatchConditions
    # Precondition Check
    if if_match == '*':
        kwargs['match_condition'] = MatchConditions.IfPresent
    else:
        kwargs['etag'] = if_match
        kwargs['match_condition'] = MatchConditions.IfNotModified
    return kwargs


def _if_none_match(if_none_match, **kwargs):
    from azure.core import MatchConditions
    if if_none_match == '*':
        kwargs['match_condition'] = MatchConditions.IfMissing
    else:
        kwargs['etag'] = if_none_match
        kwargs['match_condition'] = MatchConditions.IfModified
    return kwargs


def _encode_bytes(b):
    import base64
    if isinstance(b, (bytes, bytearray)):
        return base64.b64encode(b).decode('utf-8')
    return b


def string_to_bytes(data, encoding="utf-8"):
    if isinstance(data, str):
        return data.encode(encoding)
    return data


def transform_dict_keys_to_hump(data_dict):
    new_dict = {}
    if not data_dict:
        return new_dict
    for key in data_dict:
        new_dict[underline_to_hump(key)] = data_dict.get(key)
    return new_dict


def underline_to_hump(underline_str):
    import re
    sub = re.sub(r'(_\w)', lambda x: x.group(1)[1].upper(), underline_str)
    return sub


def list_generator(pages, num_results):
    result = []

    # get first page items
    page = list(next(pages))
    result += page

    while True:
        if not pages.continuation_token:
            break

        # handle num results
        if num_results is not None:
            if num_results == len(result):
                break

        page = list(next(pages))
        result += page

    return result


def make_file_url(client, directory_name, file_name, sas_token=None):

    if not directory_name:
        url = '{}/{}'.format(client.primary_endpoint, file_name)
    else:
        url = '{}/{}/{}'.format(client.primary_endpoint, directory_name, file_name)

    if sas_token:
        url += '?' + sas_token

    return url
