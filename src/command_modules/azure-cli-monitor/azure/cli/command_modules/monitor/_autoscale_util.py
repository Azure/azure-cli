# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.log import get_logger

logger = get_logger(__name__)


# Workaround for REST API issue: https://github.com/Azure/azure-rest-api-specs/issues/2530
AUTOSCALE_TIMEZONES = [
    {
        "name": "Dateline Standard Time",
        "offset": "-12:00"
    },
    {
        "name": "UTC-11",
        "offset": "-11:00"
    },
    {
        "name": "Aleutian Standard Time",
        "offset": "-10:00"
    },
    {
        "name": "Hawaiian Standard Time",
        "offset": "-10:00"
    },
    {
        "name": "Marquesas Standard Time",
        "offset": "-09:30"
    },
    {
        "name": "Alaskan Standard Time",
        "offset": "-09:00"
    },
    {
        "name": "UTC-09",
        "offset": "-09:00"
    },
    {
        "name": "Pacific Standard Time (Mexico)",
        "offset": "-08:00"
    },
    {
        "name": "UTC-08",
        "offset": "-08:00"
    },
    {
        "name": "Pacific Standard Time",
        "offset": "-08:00"
    },
    {
        "name": "US Mountain Standard Time",
        "offset": "-07:00"
    },
    {
        "name": "Mountain Standard Time (Mexico)",
        "offset": "-07:00"
    },
    {
        "name": "Mountain Standard Time",
        "offset": "-07:00"
    },
    {
        "name": "Central America Standard Time",
        "offset": "-06:00"
    },
    {
        "name": "Central Standard Time",
        "offset": "-06:00"
    },
    {
        "name": "Easter Island Standard Time",
        "offset": "-06:00"
    },
    {
        "name": "Central Standard Time (Mexico)",
        "offset": "-06:00"
    },
    {
        "name": "Canada Central Standard Time",
        "offset": "-06:00"
    },
    {
        "name": "SA Pacific Standard Time",
        "offset": "-05:00"
    },
    {
        "name": "Eastern Standard Time (Mexico)",
        "offset": "-05:00"
    },
    {
        "name": "Eastern Standard Time",
        "offset": "-05:00"
    },
    {
        "name": "Haiti Standard Time",
        "offset": "-05:00"
    },
    {
        "name": "Cuba Standard Time",
        "offset": "-05:00"
    },
    {
        "name": "US Eastern Standard Time",
        "offset": "-05:00"
    },
    {
        "name": "Turks and Caicos Standard Time",
        "offset": "-05:00"
    },
    {
        "name": "Paraguay Standard Time",
        "offset": "-04:00"
    },
    {
        "name": "Atlantic Standard Time",
        "offset": "-04:00"
    },
    {
        "name": "Venezuela Standard Time",
        "offset": "-04:00"
    },
    {
        "name": "Central Brazilian Standard Time",
        "offset": "-04:00"
    },
    {
        "name": "SA Western Standard Time",
        "offset": "-04:00"
    },
    {
        "name": "Pacific SA Standard Time",
        "offset": "-04:00"
    },
    {
        "name": "Newfoundland Standard Time",
        "offset": "-03:30"
    },
    {
        "name": "Tocantins Standard Time",
        "offset": "-03:00"
    },
    {
        "name": "E. South America Standard Time",
        "offset": "-03:00"
    },
    {
        "name": "SA Eastern Standard Time",
        "offset": "-03:00"
    },
    {
        "name": "Argentina Standard Time",
        "offset": "-03:00"
    },
    {
        "name": "Greenland Standard Time",
        "offset": "-03:00"
    },
    {
        "name": "Montevideo Standard Time",
        "offset": "-03:00"
    },
    {
        "name": "Magallanes Standard Time",
        "offset": "-03:00"
    },
    {
        "name": "Saint Pierre Standard Time",
        "offset": "-03:00"
    },
    {
        "name": "Bahia Standard Time",
        "offset": "-03:00"
    },
    {
        "name": "UTC-02",
        "offset": "-02:00"
    },
    {
        "name": "Mid-Atlantic Standard Time",
        "offset": "-02:00"
    },
    {
        "name": "Azores Standard Time",
        "offset": "-01:00"
    },
    {
        "name": "Cabo Verde Standard Time",
        "offset": "-01:00"
    },
    {
        "name": "Coordinated Universal Time",
        "offset": "+00:00"
    },
    {
        "name": "Morocco Standard Time",
        "offset": "+00:00"
    },
    {
        "name": "GMT Standard Time",
        "offset": "+00:00"
    },
    {
        "name": "Greenwich Standard Time",
        "offset": "+00:00"
    },
    {
        "name": "W. Europe Standard Time",
        "offset": "+01:00"
    },
    {
        "name": "Central Europe Standard Time",
        "offset": "+01:00"
    },
    {
        "name": "Romance Standard Time",
        "offset": "+01:00"
    },
    {
        "name": "Central European Standard Time",
        "offset": "+01:00"
    },
    {
        "name": "W. Central Africa Standard Time",
        "offset": "+01:00"
    },
    {
        "name": "Jordan Standard Time",
        "offset": "+02:00"
    },
    {
        "name": "GTB Standard Time",
        "offset": "+02:00"
    },
    {
        "name": "Middle East Standard Time",
        "offset": "+02:00"
    },
    {
        "name": "Egypt Standard Time",
        "offset": "+02:00"
    },
    {
        "name": "E. Europe Standard Time",
        "offset": "+02:00"
    },
    {
        "name": "Syria Standard Time",
        "offset": "+02:00"
    },
    {
        "name": "West Bank Gaza Standard Time",
        "offset": "+02:00"
    },
    {
        "name": "South Africa Standard Time",
        "offset": "+02:00"
    },
    {
        "name": "FLE Standard Time",
        "offset": "+02:00"
    },
    {
        "name": "Jerusalem Standard Time",
        "offset": "+02:00"
    },
    {
        "name": "Russia TZ 1 Standard Time",
        "offset": "+02:00"
    },
    {
        "name": "Sudan Standard Time",
        "offset": "+02:00"
    },
    {
        "name": "Libya Standard Time",
        "offset": "+02:00"
    },
    {
        "name": "Namibia Standard Time",
        "offset": "+02:00"
    },
    {
        "name": "Arabic Standard Time",
        "offset": "+03:00"
    },
    {
        "name": "Turkey Standard Time",
        "offset": "+03:00"
    },
    {
        "name": "Arab Standard Time",
        "offset": "+03:00"
    },
    {
        "name": "Belarus Standard Time",
        "offset": "+03:00"
    },
    {
        "name": "Russia TZ 2 Standard Time",
        "offset": "+03:00"
    },
    {
        "name": "E. Africa Standard Time",
        "offset": "+03:00"
    },
    {
        "name": "Iran Standard Time",
        "offset": "+03:30"
    },
    {
        "name": "Arabian Standard Time",
        "offset": "+04:00"
    },
    {
        "name": "Astrakhan Standard Time",
        "offset": "+04:00"
    },
    {
        "name": "Azerbaijan Standard Time",
        "offset": "+04:00"
    },
    {
        "name": "Russia TZ 3 Standard Time",
        "offset": "+04:00"
    },
    {
        "name": "Mauritius Standard Time",
        "offset": "+04:00"
    },
    {
        "name": "Saratov Standard Time",
        "offset": "+04:00"
    },
    {
        "name": "Georgian Standard Time",
        "offset": "+04:00"
    },
    {
        "name": "Caucasus Standard Time",
        "offset": "+04:00"
    },
    {
        "name": "Afghanistan Standard Time",
        "offset": "+04:30"
    },
    {
        "name": "West Asia Standard Time",
        "offset": "+05:00"
    },
    {
        "name": "Russia TZ 4 Standard Time",
        "offset": "+05:00"
    },
    {
        "name": "Pakistan Standard Time",
        "offset": "+05:00"
    },
    {
        "name": "India Standard Time",
        "offset": "+05:30"
    },
    {
        "name": "Sri Lanka Standard Time",
        "offset": "+05:30"
    },
    {
        "name": "Nepal Standard Time",
        "offset": "+05:45"
    },
    {
        "name": "Central Asia Standard Time",
        "offset": "+06:00"
    },
    {
        "name": "Bangladesh Standard Time",
        "offset": "+06:00"
    },
    {
        "name": "Omsk Standard Time",
        "offset": "+06:00"
    },
    {
        "name": "Myanmar Standard Time",
        "offset": "+06:30"
    },
    {
        "name": "SE Asia Standard Time",
        "offset": "+07:00"
    },
    {
        "name": "Altai Standard Time",
        "offset": "+07:00"
    },
    {
        "name": "W. Mongolia Standard Time",
        "offset": "+07:00"
    },
    {
        "name": "Russia TZ 6 Standard Time",
        "offset": "+07:00"
    },
    {
        "name": "Novosibirsk Standard Time",
        "offset": "+07:00"
    },
    {
        "name": "Tomsk Standard Time",
        "offset": "+07:00"
    },
    {
        "name": "China Standard Time",
        "offset": "+08:00"
    },
    {
        "name": "Russia TZ 7 Standard Time",
        "offset": "+08:00"
    },
    {
        "name": "Malay Peninsula Standard Time",
        "offset": "+08:00"
    },
    {
        "name": "W. Australia Standard Time",
        "offset": "+08:00"
    },
    {
        "name": "Taipei Standard Time",
        "offset": "+08:00"
    },
    {
        "name": "Ulaanbaatar Standard Time",
        "offset": "+08:00"
    },
    {
        "name": "North Korea Standard Time",
        "offset": "+08:30"
    },
    {
        "name": "Aus Central W. Standard Time",
        "offset": "+08:45"
    },
    {
        "name": "Transbaikal Standard Time",
        "offset": "+09:00"
    },
    {
        "name": "Tokyo Standard Time",
        "offset": "+09:00"
    },
    {
        "name": "Korea Standard Time",
        "offset": "+09:00"
    },
    {
        "name": "Russia TZ 8 Standard Time",
        "offset": "+09:00"
    },
    {
        "name": "Cen. Australia Standard Time",
        "offset": "+09:30"
    },
    {
        "name": "AUS Central Standard Time",
        "offset": "+09:30"
    },
    {
        "name": "E. Australia Standard Time",
        "offset": "+10:00"
    },
    {
        "name": "AUS Eastern Standard Time",
        "offset": "+10:00"
    },
    {
        "name": "West Pacific Standard Time",
        "offset": "+10:00"
    },
    {
        "name": "Tasmania Standard Time",
        "offset": "+10:00"
    },
    {
        "name": "Russia TZ 9 Standard Time",
        "offset": "+10:00"
    },
    {
        "name": "Lord Howe Standard Time",
        "offset": "+10:30"
    },
    {
        "name": "Bougainville Standard Time",
        "offset": "+11:00"
    },
    {
        "name": "Russia TZ 10 Standard Time",
        "offset": "+11:00"
    },
    {
        "name": "Magadan Standard Time",
        "offset": "+11:00"
    },
    {
        "name": "Norfolk Standard Time",
        "offset": "+11:00"
    },
    {
        "name": "Sakhalin Standard Time",
        "offset": "+11:00"
    },
    {
        "name": "Central Pacific Standard Time",
        "offset": "+11:00"
    },
    {
        "name": "Russia TZ 11 Standard Time",
        "offset": "+12:00"
    },
    {
        "name": "New Zealand Standard Time",
        "offset": "+12:00"
    },
    {
        "name": "UTC+12",
        "offset": "+12:00"
    },
    {
        "name": "Fiji Standard Time",
        "offset": "+12:00"
    },
    {
        "name": "Kamchatka Standard Time",
        "offset": "+12:00"
    },
    {
        "name": "Chatham Islands Standard Time",
        "offset": "+12:45"
    },
    {
        "name": "UTC+13",
        "offset": "+13:00"
    },
    {
        "name": "Tonga Standard Time",
        "offset": "+13:00"
    },
    {
        "name": "Samoa Standard Time",
        "offset": "+13:00"
    },
    {
        "name": "Line Islands Standard Time",
        "offset": "+14:00"
    }
]


def build_autoscale_profile(autoscale_settings):
    """ Builds up a logical model of the autoscale weekly schedule. This then has to later be
        translated into objects that work with the Monitor autoscale API. """
    from datetime import time
    import json
    from azure.mgmt.monitor.models import AutoscaleProfile

    def _validate_default_profile(default_profile, profile):
        if profile.capacity.default != default_profile.capacity.default or \
                profile.capacity.minimum != default_profile.capacity.minimum or \
                profile.capacity.maximum != default_profile.capacity.maximum:
            from knack.util import CLIError
            raise CLIError('unable to resolve default profile.')

    recurring_profiles = [x for x in autoscale_settings.profiles if x.recurrence]
    default_profiles = [x for x in autoscale_settings.profiles if not x.recurrence and not x.fixed_date]

    profile_schedule = {
    }

    # find the default profile and ensure that if there are multiple, they are consistent
    default_profile = default_profiles[0] if default_profiles else None
    for p in default_profiles:
        _validate_default_profile(default_profile, p)

    for profile in recurring_profiles:
        # portal creates extra default profiles with JSON names...
        # trying to stay compatible with that
        try:
            # portal-created "default" or end time
            json_name = json.loads(profile.name)
            sched_name = json_name['for']
            end_time = time(hour=profile.recurrence.schedule.hours[0], minute=profile.recurrence.schedule.minutes[0])

            if not default_profile:
                # choose this as default if it is the first
                default_profile = AutoscaleProfile(
                    name='default',
                    capacity=profile.capacity,
                    rules=profile.rules
                )
            else:
                # otherwise ensure it is consistent with the one chosen earlier
                _validate_default_profile(default_profile, profile)

            for day in profile.recurrence.schedule.days:
                if day not in profile_schedule:
                    profile_schedule[day] = {}
                if sched_name in profile_schedule[day]:
                    profile_schedule[day][sched_name]['end'] = end_time
                else:
                    profile_schedule[day][sched_name] = {'end': end_time}
        except ValueError:
            # start time
            sched_name = profile.name
            start_time = time(hour=profile.recurrence.schedule.hours[0], minute=profile.recurrence.schedule.minutes[0])
            for day in profile.recurrence.schedule.days:
                if day not in profile_schedule:
                    profile_schedule[day] = {}
                if sched_name in profile_schedule[day]:
                    profile_schedule[day][sched_name]['start'] = start_time
                    profile_schedule[day][sched_name]['capacity'] = profile.capacity
                    profile_schedule[day][sched_name]['rules'] = profile.rules
                else:
                    profile_schedule[day][sched_name] = {
                        'start': start_time,
                        'capacity': profile.capacity,
                        'rules': profile.rules
                    }

    return default_profile, profile_schedule


def validate_autoscale_profile(schedule, start, end, recurrence):
    """ Check whether the proposed schedule conflicts with existing schedules. If so,
        issue a warning. """
    # pylint: disable=cell-var-from-loop
    for day in recurrence.schedule.days:
        if day not in schedule:
            schedule[day] = {}

        def _find_conflicting_profile(time):
            conflict_sched = None
            for sched_name, sched_values in schedule[day].items():
                if time >= sched_values['start'] and time <= sched_values['end']:
                    conflict_sched = sched_name
            return conflict_sched

        def _profile_is_subset(profile, start, end):
            return profile['start'] >= start and profile['end'] <= end

        # check if start or end dates fall within an existing schedule
        # check is proposed schedule engulfs any existing schedules
        profile_conflicts = [k for k, v in schedule[day].items() if _profile_is_subset(v, start, end)]
        start_conflict = _find_conflicting_profile(start)
        if start_conflict:
            profile_conflicts.append(start_conflict)
        end_conflict = _find_conflicting_profile(end)
        if end_conflict:
            profile_conflicts.append(end_conflict)

        if profile_conflicts:
            logger.warning("Proposed schedule '%s %s-%s' has a full or partial overlap with the following existing "
                           "schedules: %s. Unexpected behavior may occur.",
                           day, start, end, ', '.join(profile_conflicts))
