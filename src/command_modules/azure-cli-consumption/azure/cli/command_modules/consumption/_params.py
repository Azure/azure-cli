# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from azure.cli.core.commands import register_cli_argument
from ._validators import get_datetime_type

register_cli_argument('consumption usage list', 'top', options_list=('--top', '-t'), type=int, help='maximum number of items to return. Accepted range for this value is 1 - 1000')
register_cli_argument('consumption usage list', 'include_additional_properties', options_list=('--include-additional-properties', '-a'), action='store_true', help='include additional properties in the usages')
register_cli_argument('consumption usage list', 'include_meter_details', options_list=('--include-meter-details', '-m'), action='store_true', help='include meter details in the usages')
register_cli_argument('consumption usage list', 'start_date', options_list=('--start-date', '-s'), type=get_datetime_type(), help='start date (in UTC Y-m-d) of the usages')
register_cli_argument('consumption usage list', 'end_date', options_list=('--end-date', '-e'), type=get_datetime_type(), help='end date (in UTC Y-m-d) of the usages')
register_cli_argument('consumption usage list', 'invoice_name', options_list=('--invoice-name', '-i'), help='name of a specific invoice to get the usage details that associate with')
register_cli_argument('consumption usage list', 'billing_period_name', options_list=('--billing-period-name', '-p'), help='name of a specific billing period to get the usage details that associate with')
