# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from datetime import datetime

# Argument types


def datetime_type(string):
    """ Validates UTC datettime in accepted format. Examples: 31-12-2017 """
    accepted_date_formats = ['%d-%m-%Y']
    for form in accepted_date_formats:
        try:
            return datetime.strptime(string, form)
        except ValueError:  # checks next format
            pass
    raise ValueError("Input '{}' not valid. Valid example: 31-12-2017".format(string))
