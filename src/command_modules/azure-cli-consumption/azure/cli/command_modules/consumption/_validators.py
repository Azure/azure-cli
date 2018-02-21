# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
from datetime import datetime
from azure.cli.core.util import CLIError


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

def get_parameters_type():
    def parameters_type(string):        
        parameters = json.loads(string)
        print (string)
        return parameters_type

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


def validate_both_start_end_dates(namespace):
    """Validates the existence of both start and end dates in the parameter or neither"""
    if bool(namespace.start_date) != bool(namespace.end_date):
        raise CLIError("usage error: Both --start-date and --end-date need to be supplied or neither.")


def validate_reservations_summaries(namespace):
    """lowercase the data grain for comparison"""
    data_grain = namespace.grain.lower()
    if data_grain != 'daily' and data_grain != 'monthly':
        raise CLIError("usage error: --grain  can be either daily or monthly.")
    if data_grain == 'daily' and (not namespace.start_date or not namespace.end_date):
        raise CLIError("usage error: Both --start-date and --end-date need to be supplied for daily grain.")


def validate_budget_parameters(namespace):
    """lowercase the time grain for comparison"""
    print(namespace.parameters)
    parameters = json.loads(namespace.parameters)
    time_grain = parameters.time_grain.lower()
    if time_grain != 'annually' and time_grain != 'quarterly' and time_grain != 'monthly':
        raise CLIError("usage error: --parameters.time_grain must be specified and values can be either 'Annually', 'Quaterly', or 'Monthly'.")
    time_period = namespace.parameters.time_period
    try:
        datetime_type(time_period.start_date)
    except ValueError:
        raise CLIError("usage error: --parameters.time_period.start_date is not valid. start date must be specified")
    try:
        datetime_type(time_period.end_date)
    except ValueError:
        raise CLIError("usage error: --parameters.time_period.end_date is not valid. end date must be specified")
    if amount < 0:
        raise CLIError("usage error: --parameters.time_period.amount must be greater than 0")
    budgetcategory = namespace.parameters.category.lower()
    if budgetcategory != 'cost' and budgetcategory != 'usage':
        raise CLIError("usage error: --parameters.category must be set to either cost or usage")
    