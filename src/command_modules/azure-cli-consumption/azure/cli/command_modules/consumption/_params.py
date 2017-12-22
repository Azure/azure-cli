# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from ._validators import get_datetime_type


def load_arguments(self, _):
    with self.argument_context('consumption usage list') as c:
        c.argument('top', options_list=['--top', '-t'], type=int, help='maximum number of items to return. Accepted range for this value is 1 - 1000')
        c.argument('include_additional_properties', options_list=['--include-additional-properties', '-a'], action='store_true', help='include additional properties in the usages')
        c.argument('include_meter_details', options_list=['--include-meter-details', '-m'], action='store_true', help='include meter details in the usages')
        c.argument('start_date', options_list=['--start-date', '-s'], type=get_datetime_type(), help='start date (in UTC Y-m-d) of the usages. Both start date and end date need to be supplied or neither')
        c.argument('end_date', options_list=['--end-date', '-e'], type=get_datetime_type(), help='end date (in UTC Y-m-d) of the usages. Both start date and end date need to be supplied or neither')
        c.argument('billing_period_name', options_list=['--billing-period-name', '-p'], help='name of a specific billing period to get the usage details that associate with')
    with self.argument_context('consumption reservations summaries list') as rs:
        rs.argument('reservationorderid', options_list=['--reservation-order-id', '-r'], help='Reservation order id')
        rs.argument('reservationid', options_list=['--reservation-id', '-i'], help='Reservation id')
        rs.argument('start_date', options_list=['--start-date', '-s'], type=get_datetime_type(), help='start date (in UTC Y-m-d) of the reservation summaries. Only needed for daily grain and both start date and end date need to be supplied or neither')
        rs.argument('end_date', options_list=['--end-date', '-e'], type=get_datetime_type(), help='end date (in UTC Y-m-d) of the reservation summaries. Only needed for daily grain and both start date and end date need to be supplied or neither')
        rs.argument('grain', options_list=['--grain', '-g'], type=str, help='Reservation summaries grain. Possible values are daily or monthly')
    with self.argument_context('consumption reservations details list') as rd:
        rd.argument('reservationorderid', options_list=['--reservation-order-id', '-r'], help='Reservation order id')
        rd.argument('reservationid', options_list=['--reservation-id', '-i'], help='Reservation id')
        rd.argument('start_date', options_list=['--start-date', '-s'], type=get_datetime_type(), help='start date (in UTC Y-m-d) of the reservation summaries. Only needed for daily grain and both start date and end date need to be supplied or neither')
        rd.argument('end_date', options_list=['--end-date', '-e'], type=get_datetime_type(), help='end date (in UTC Y-m-d) of the reservation summaries. Only needed for daily grain and both start date and end date need to be supplied or neither')
