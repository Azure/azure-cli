# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from datetime import datetime


def get_datetime_type():
    """ Validates UTC datetime. Examples of accepted forms:
    2017-12-31T01:11:59Z,2017-12-31T01:11Z or 2017-12-31T01Z or 2017-12-31 """
    def datetime_type(string):
        """ Validates UTC datetime. Examples of accepted forms:
        2017-12-31T01:11:59Z,2017-12-31T01:11Z or 2017-12-31T01Z or 2017-12-31 """
        accepted_date_formats = ['%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%dT%H:%MZ',
                                 '%Y-%m-%dT%HZ', '%Y-%m-%d']
        for form in accepted_date_formats:
            try:
                return datetime.strptime(string, form)
            except ValueError:
                continue
        raise ValueError("Input '{}' not valid. Valid example: 2017-02-11T23:59:59Z".format(string))
    return datetime_type
