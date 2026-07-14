# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Human-readable report rendering for 'az webapp troubleshoot status --report'.

Extracted from ``custom.py`` to keep the command's control flow separate from
its presentation layer. The command builds a structured payload; this module
renders it. ``render_report(payload)`` is the sole public entry point.
"""

import re
import shutil
import sys
import textwrap
from datetime import datetime, timezone

from azure.cli.core.style import Style, print_styled_text


def render_report(payload):
    """Print the human-readable report (Site Runtime Status + per-instance Startup summary).
    Invoked by 'az webapp troubleshoot status' when --report is passed."""
    instances = payload.get('instances') or []
    app_name = payload.get('name') or '<webapp>'
    resource_group = payload.get('resourceGroup')

    def _out(*objs):
        print_styled_text(*objs, file=sys.stdout)

    def _row(*objs):
        _out(list(objs))

    if not instances:
        orphan_startups = payload.get('orphanStartups') or []
        rg = resource_group or '<resource-group>'
        if not orphan_startups:
            _out((Style.PRIMARY, "No per-instance runtime status was returned for '{}'.".format(app_name)))
            _out('  ARM /siteStatus returned no entries. This is typical for an app that is')
            _out('  running normally without recent state transitions or startup failures.')
            _out((Style.WARNING, '▶ Hint:'))
            _out('  Check application logs:  az webapp log tail -n {} -g {}'.format(app_name, rg))
            _out('  Check startup logs:      az webapp log startup show -n {} -g {}'.format(app_name, rg))
            return
        # ARM had nothing but SCM did — fall through so the orphan block below
        # still renders. Give the user a heads-up first so the header makes sense.
        _out('')
        _out((Style.PRIMARY, "ARM /siteStatus returned no entries for '{}', but startup".format(app_name)))
        _out((Style.PRIMARY, '  summaries were available from SCM (shown below).'))
        _out('')
    else:
        _out('')
        _out((Style.HIGHLIGHT, "Application status for {}.".format(app_name)))
        _out('')

    # Overview table (skip when only one instance is present, e.g. --instance filter).
    if len(instances) > 1:
        col_widths = (14, 20, 12, 24)
        header = "{:<{w0}}{:<{w1}}{:<{w2}}{}".format(
            'INSTANCE', 'MACHINE', 'STATE', 'UPDATED',
            w0=col_widths[0], w1=col_widths[1], w2=col_widths[2])
        _out((Style.PRIMARY, header))
        _out((Style.PRIMARY, '-' * sum(col_widths)))
        for inst in instances:
            startup = inst.get('startup') or {}
            updated = _format_dt(_most_recent_startup(startup)) or '-'
            state = inst.get('state') or '-'
            # Pad plain text first, then wrap the STATE segment in its style — the
            # framework's color escapes don't perturb the visible column width.
            _out([
                (Style.PRIMARY, '{:<{w}}'.format(_short_id(inst.get('instanceId')), w=col_widths[0])),
                (Style.PRIMARY, '{:<{w}}'.format(inst.get('machineName') or '-', w=col_widths[1])),
                (_state_style(state), '{:<{w}}'.format(state, w=col_widths[2])),
                (Style.PRIMARY, updated),
            ])
        _out('')
        _out('')

    # Per-instance Site Runtime Status + Startup summary.
    for inst in instances:
        machine = inst.get('machineName')
        label = machine if machine else _short_id(inst.get('instanceId'))
        scm_id = inst.get('startupInstanceId')
        # When ARM's machineName and SCM's InstanceId disagree (common on
        # Linux App Service — ARM tracks the worker slot, KuduLite tracks the
        # container) surface both so users can correlate with SCM logs.
        _out("-" * 76)
        if scm_id and scm_id != machine:
            header = 'Instance {} Full Status Report (SCM: {}) '.format(label, scm_id)
        else:
            header = 'Instance {} Full Status Report '.format(label)
        _out(header)
        _out("-" * 76)
        _out((Style.HIGHLIGHT, 'Last runtime status'))
        _print_runtime_block(inst, _out)
        _out('')
        _out((Style.HIGHLIGHT, 'Startup summary (last 24h)'))
        if not machine and not inst.get('startup'):
            # Without machineName we couldn't query KuduLite for this instance, so
            # distinguish the "couldn't ask" case from "asked, nothing recorded".
            _out('  Startup summary unavailable: machine name could not be determined for this instance.')
            _out('')
        else:
            _print_startup_block(inst.get('startup'), _out)
        _out()
        _out()

    # Orphan startups — SCM entries with no matching ARM instance. These
    # commonly show up when a container has been recycled: SCM still has the
    # last container's logs, but ARM has already replaced the worker-slot ID.
    orphan_startups = payload.get('orphanStartups') or []
    for orphan in orphan_startups:
        scm_id = orphan.get('InstanceId') or '<unknown>'
        _out((Style.HIGHLIGHT, 'Instance {} Startup Summary (no matching ARM instance)'.format(scm_id)))
        _row((Style.HIGHLIGHT, '─' * 76))
        _out((Style.HIGHLIGHT, 'Startup summary (last 24h)'))
        _print_startup_block(orphan.get('Startup'), _out)
        _out()

    # Hint footer — surfaced only when at least one instance has a real
    # failure in the report's window (Failed > 0 + lastError set).
    has_error = any(
        (inst.get('lastError') and _failed_count(inst.get('startup')) > 0)
        for inst in instances
    )
    if has_error:
        rg = resource_group or '<resource-group>'
        _out((Style.WARNING, '▶ Hint:'))
        _out('  Check application logs:  az webapp log tail -n {} -g {}'.format(app_name, rg))
        _out('  Check startup logs:      az webapp log startup show -n {} -g {}'.format(app_name, rg))


def _state_style(state):
    """Map a runtime state string to an azure-cli Style for print_styled_text."""
    if not state:
        return Style.PRIMARY
    s = state.lower()
    if s == 'started':
        return Style.SUCCESS
    if s in ('stopped', 'failed', 'crashed', 'unhealthy'):
        return Style.ERROR
    if s in ('starting', 'pullingimage', 'pulling', 'pending'):
        return Style.WARNING
    return Style.PRIMARY


def _outcome_style(outcome):
    if not outcome:
        return Style.PRIMARY
    o = outcome.upper()
    if o == 'STARTED':
        return Style.SUCCESS
    if o in ('FAILED', 'CRASHED'):
        return Style.ERROR
    return Style.PRIMARY


def _count_style(count, kind):
    """Style for a numeric count. kind='failed' -> ERROR when > 0; 'successful' -> SUCCESS when > 0.
    Accepts either an int/str integer (e.g. 3, "3") or a KuduLite capped-count
    string like "50+" (parsed as the leading integer for the > 0 test)."""
    text = str(count)
    try:
        n = int(text)
    except (TypeError, ValueError):
        # Handle capped forms like "50+" — parse the leading digits.
        m = re.match(r'\d+', text)
        n = int(m.group(0)) if m else None
    if n is None:
        return Style.PRIMARY, text
    if kind == 'failed' and n > 0:
        return Style.ERROR, text
    if kind == 'successful' and n > 0:
        return Style.SUCCESS, text
    return Style.PRIMARY, text


def _short_id(instance_id):
    """Truncate a long hex ARM instanceId for table display."""
    if not instance_id:
        return '-'
    if len(instance_id) > 12:
        return instance_id[:10]
    return instance_id


def _format_dt(value):
    if not value:
        return None
    # Pass through ISO strings; trim sub-second/timezone noise for the table view.
    if isinstance(value, str):
        v = value.replace('T', ' ')
        is_utc = v.endswith('Z')
        if '.' in v:
            v = v.split('.', 1)[0]
        if is_utc:
            if v.endswith('Z'):
                v = v[:-1]
            v = v + ' UTC'
        elif '+' in v:
            v = v.split('+', 1)[0]
        return v
    return str(value)


def _relative_age(iso_value):
    """Return a short 'Nh Mm ago' / 'Nm ago' / 'just now' / 'in the future' string
    for an ISO-8601 UTC timestamp, or None if the input is unparseable/missing."""
    if not iso_value or not isinstance(iso_value, str):
        return None
    v = iso_value
    if '.' in v:
        # datetime.fromisoformat pre-3.11 chokes on fractional seconds with 'Z' — strip both.
        head, _, tail = v.partition('.')
        tz = ''
        for suffix in ('Z', '+', '-'):
            if suffix in tail:
                idx = tail.find(suffix)
                tz = tail[idx:]
                break
        v = head + tz
    v = v.replace('Z', '+00:00')
    try:
        dt = datetime.fromisoformat(v)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    delta = datetime.now(timezone.utc) - dt
    total_seconds = int(delta.total_seconds())
    if total_seconds < 0:
        return 'in the future'
    if total_seconds < 60:
        return 'just now'
    minutes = total_seconds // 60
    if minutes < 60:
        return '{}m ago'.format(minutes)
    hours = minutes // 60
    rem_min = minutes % 60
    if hours < 24:
        return '{}h {}m ago'.format(hours, rem_min) if rem_min else '{}h ago'.format(hours)
    days = hours // 24
    rem_hr = hours % 24
    return '{}d {}h ago'.format(days, rem_hr) if rem_hr else '{}d ago'.format(days)


def _failed_count(startup):
    """Parse Startup.Failed into an int (0 when missing/invalid). Accepts int,
    numeric string, or KuduLite's capped '50+' form (leading digits win)."""
    if not startup:
        return 0
    raw = startup.get('Failed')
    if raw is None:
        return 0
    text = str(raw)
    try:
        return int(text)
    except ValueError:
        m = re.match(r'\d+', text)
        return int(m.group(0)) if m else 0


def _emit_labeled(emit, label, value, value_style=None):
    """Emit '<label><value>' with hanging indent: if the value wraps at the
    terminal width, continuation lines are aligned under the value column."""
    text = value if value is not None else ''
    if not isinstance(text, str):
        text = str(text)

    term_w = shutil.get_terminal_size(fallback=(120, 40)).columns
    indent = ' ' * len(label)
    body_w = max(20, term_w - len(label))
    lines = textwrap.wrap(text, width=body_w) or [text]

    if value_style is not None:
        emit([(Style.PRIMARY, label), (value_style, lines[0])])
        for cont in lines[1:]:
            emit([(Style.PRIMARY, indent), (value_style, cont)])
    else:
        emit('{}{}'.format(label, lines[0]))
        for cont in lines[1:]:
            emit('{}{}'.format(indent, cont))


def _print_runtime_block(inst, emit):
    """Print one Site Runtime Status block from an ARM /siteStatus item."""
    if not inst:
        emit('  (no runtime status reported)')
        return
    state = inst.get('state') or '-'
    details = inst.get('details') or '-'
    emit([(Style.PRIMARY, '  State                '), (_state_style(state), state)])
    _emit_labeled(emit, '  Details              ', details)
    # LastError may be stale after a recovery, so only surface it when this
    # worker has actually had failed startup attempts in the report's window.
    has_visible_error = bool(inst.get('lastError')) and _failed_count(inst.get('startup')) > 0
    if has_visible_error:
        last_error = inst.get('lastError') or '-'
        last_error_details = inst.get('lastErrorDetails') or '-'
        # Treat .NET DateTime.MinValue (0001-01-01...) as "no error ever" and hide it.
        last_error_ts_raw = inst.get('lastErrorTimestamp')
        if isinstance(last_error_ts_raw, str) and last_error_ts_raw.startswith('0001-01-01'):
            last_error_ts_raw = None
        last_error_ts = _format_dt(last_error_ts_raw) or '-'
        age = _relative_age(last_error_ts_raw) if last_error_ts_raw else None
        if age:
            last_error_ts = '{} ({})'.format(last_error_ts, age)
        _emit_labeled(emit, '  Last Error           ', last_error)
        _emit_labeled(emit, '  Last Error Details   ', last_error_details)
        _emit_labeled(emit, '  Last Error Timestamp ', last_error_ts)


def _most_recent_startup(startup):
    """Return the most recent of MostRecentSuccess / MostRecentFailure (ISO strings),
    or None if both are missing. Lexicographic max is correct for RFC3339/ISO-8601 UTC."""
    if not startup:
        return None
    candidates = [ts for ts in (startup.get('MostRecentSuccess'),
                                startup.get('MostRecentFailure')) if ts]
    return max(candidates) if candidates else None


def _startup_fetch_failed(startup):
    """Return the SummaryFetchStatus string only when it indicates a fetch failure
    (i.e. not the KuduLite success sentinel). None means success or missing."""
    if not startup:
        return None
    status = startup.get('SummaryFetchStatus')
    if not status:
        return None
    # KuduLite success sentinel starts with 'Successfully'; anything else is a
    # user-facing failure reason we want to surface.
    if str(status).startswith('Successfully'):
        return None
    return status


def _print_startup_block(s, emit):
    if not s:
        emit('  No startup attempts recorded in the last 24 hours')
        emit('')
        return
    # KuduLite sets SummaryFetchStatus to a failure reason when it couldn't read
    # the log directory for this worker; other fields are meaningless then.
    fetch_error = _startup_fetch_failed(s)
    if fetch_error:
        emit([(Style.WARNING, '  ' + str(fetch_error))])
        emit('')
        return
    succeeded = s.get('Succeeded', 0)
    failed = s.get('Failed', 0)
    emit([(Style.PRIMARY, '  Succeeded              '), _count_style(succeeded, 'successful')])
    emit([(Style.PRIMARY, '  Failed                 '), _count_style(failed, 'failed')])
    most_recent_success = _format_dt(s.get('MostRecentSuccess'))
    most_recent_failure = _format_dt(s.get('MostRecentFailure'))
    emit([(Style.PRIMARY, '  Most recent success    '),
          (_outcome_style('STARTED') if most_recent_success else Style.PRIMARY,
           most_recent_success or '-')])
    emit([(Style.PRIMARY, '  Most recent failure    '),
          (_outcome_style('FAILED') if most_recent_failure else Style.PRIMARY,
           most_recent_failure or '-')])
    emit('')
