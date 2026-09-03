# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Human-readable report rendering for 'az webapp troubleshoot config --report'.

Extracted from ``custom.py`` to keep the command's control flow separate from
its presentation layer. The command builds a structured payload; this module
renders it. ``render_report(payload)`` is the sole public entry point.
"""

import shutil
import sys
import textwrap
from datetime import datetime, timezone

from azure.cli.core.style import Style, print_styled_text


def _format_dt(value):
    """Human-readable timestamp: 'YYYY-MM-DD HH:MM:SS UTC' (or best-effort)."""
    if not value:
        return None
    if isinstance(value, str):
        v = value.replace('T', ' ')
        is_utc = v.endswith('Z')
        if '.' in v:
            v = v.split('.', 1)[0]
        if is_utc:
            if v.endswith('Z'):
                v = v[:-1]
            v = v + ' UTC'
        elif v.endswith('+00:00'):
            v = v[:-6] + ' UTC'
        elif '+' in v:
            v = v.split('+', 1)[0]
        return v
    return str(value)


def _short_id(instance_id):
    """Truncate a long hex ARM instanceId to 10 characters for display."""
    if not instance_id:
        return None
    if len(instance_id) > 12:
        return instance_id[:10]
    return instance_id


def _relative_age(iso_value):
    """Return a short 'Nh Mm ago' / 'Nm ago' / 'just now' / 'in the future' string
    for an ISO-8601 UTC timestamp, or None if the input is unparseable/missing."""
    if not iso_value or not isinstance(iso_value, str):
        return None
    v = iso_value
    if '.' in v:
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
    rem_hours = hours % 24
    return '{}d {}h ago'.format(days, rem_hours) if rem_hours else '{}d ago'.format(days)


def render_report(payload):
    """Print the human-readable report: BUILT-IN CHECKS + SITE RUNTIME ERROR
    RECOMMENDATION. Invoked when ``--report`` is passed."""

    def _out(*objs):
        print_styled_text(*objs, file=sys.stdout)

    def _row(*objs):
        _out(list(objs))

    def _labeled(label, value, style=Style.PRIMARY):
        """Emit '<label><value>' with hanging indent so wrapped continuation
        lines align under the value column."""
        text = '' if value is None else str(value)
        term_w = shutil.get_terminal_size(fallback=(120, 40)).columns
        indent = ' ' * len(label)
        body_w = max(20, term_w - len(label))
        lines = textwrap.wrap(text, width=body_w) or [text]
        _row((style, label), (style, lines[0]))
        for cont in lines[1:]:
            _row((style, indent), (style, cont))

    config_check = payload.get('configCheck') or {}
    config_check_failed = payload.get('configCheck') is None
    config_check_status = payload.get('configCheckStatus')
    config_check_message = payload.get('configCheckMessage')
    settings = config_check.get('Settings') or config_check.get('settings') or []
    if not isinstance(settings, list):
        settings = []
    settings = [s for s in settings if isinstance(s, dict)]
    runtime_error = payload.get('runtimeError')

    def _details_level(setting):
        # KuduLite tags each check with DetailsLevel: 'info' | 'warning' | 'error'.
        raw = setting.get('DetailsLevel')
        if raw is None:
            raw = setting.get('detailsLevel')
        if isinstance(raw, str):
            level = raw.strip().lower()
            if level in ('info', 'warning', 'error'):
                return level
        return 'info'

    def _style_for_level(level):
        if level == 'error':
            return Style.ERROR
        if level == 'warning':
            return Style.WARNING
        return Style.SUCCESS

    def _is_issue(level):
        return level in ('warning', 'error')

    any_issue = any(_is_issue(_details_level(s)) for s in settings)

    # Show the runtime error section only when the ARM lastErrorTimestamp is
    # within the freshness window. The payload already carries the pre-computed
    # 'isRecent' signal so structured-payload consumers can apply the same gate
    # (see _RUNTIME_ERROR_FRESHNESS_MINUTES / _runtime_error_is_recent in custom.py).
    show_runtime = bool(runtime_error and runtime_error.get('isRecent'))

    # ---- Section 1: Built-in checks ----
    _out()
    _row((Style.HIGHLIGHT, '═══ BUILT-IN CHECKS ' + '═' * 55))
    _out()
    if not config_check_failed:
        machine_name = config_check.get('MachineName') or config_check.get('machineName')
        requested_machine_name = payload.get('requestedMachineName')
        instance_id = config_check.get('InstanceId') or config_check.get('instanceId')
        written_at_raw = config_check.get('WrittenAt') or config_check.get('writtenAt')
        if isinstance(machine_name, str):
            machine_name = machine_name.strip()
        if isinstance(requested_machine_name, str):
            requested_machine_name = requested_machine_name.strip()
        if isinstance(written_at_raw, str):
            written_at_raw = written_at_raw.strip()
        instance_value = machine_name or requested_machine_name or _short_id(instance_id)
        if instance_value:
            _labeled('Instance:     ', instance_value, Style.HIGHLIGHT)
        if written_at_raw:
            written_at = _format_dt(written_at_raw) or str(written_at_raw)
            _labeled('Last Updated: ', written_at, Style.HIGHLIGHT)
        if machine_name or written_at_raw:
            _out()

    if config_check_failed:
        if config_check_status == 404:
            message = config_check_message or (
                'Configuration check feature is currently disabled. Please try again later.')
            _row((Style.WARNING, message))
        else:
            _row((Style.WARNING,
                  'Failed to retrieve built-in configuration checks. Please try again. '
                  'If the issue persists, restart the application (\'az webapp restart\') and confirm the SCM (Kudu) '
                  'is running and reachable.'))
    elif not settings:
        _row((Style.WARNING, 'No built-in configuration checks reported.'))
    else:
        term_w = shutil.get_terminal_size(fallback=(120, 40)).columns
        setting_w = max(20, min(40, max(len(str(s.get('Setting') or '')) for s in settings) + 2))
        value_w = max(15, min(30, max(len(str(s.get('Value') or '')) for s in settings) + 2))

        header = '{sname:<{sw}}{vname:<{vw}}{dname}'.format(
            sname='Setting', sw=setting_w, vname='Value', vw=value_w, dname='Details')
        _row((Style.HIGHLIGHT, header))
        _row((Style.SECONDARY, '{s}{v}{d}'.format(
            s=('─' * (setting_w - 2)).ljust(setting_w),
            v=('─' * (value_w - 2)).ljust(value_w),
            d='─' * 40)))
        for setting in settings:
            name_v = str(setting.get('Setting') or '')
            value_v = str(setting.get('Value') if setting.get('Value') is not None else '')
            details_v = str(setting.get('Details') or '')
            details_style = _style_for_level(_details_level(setting))
            prefix = '{s:<{sw}}{v:<{vw}}'.format(
                s=name_v, sw=setting_w, v=value_v, vw=value_w)
            details_w = max(20, term_w - len(prefix))
            detail_lines = textwrap.wrap(details_v, width=details_w) or [details_v]
            _row((Style.PRIMARY, prefix), (details_style, detail_lines[0]))
            cont_indent = ' ' * len(prefix)
            for cont in detail_lines[1:]:
                _row((Style.PRIMARY, cont_indent), (details_style, cont))

    # ---- Section 2: Site runtime error recommendation ----
    # Rendered only when the ARM lastErrorTimestamp is within the last 15
    # minutes. Applied consistently regardless of whether the built-in
    # checks succeeded, failed, or reported no issues.
    if show_runtime:
        _out()
        _out()
        _row((Style.HIGHLIGHT, '═══ SITE RUNTIME ERROR RECOMMENDATION ' + '═' * 37))
        _out()
        state = str(runtime_error.get('state') or '')
        last_error = str(runtime_error.get('lastError') or '')
        details = str(runtime_error.get('lastErrorDetails') or '')
        timestamp_raw = runtime_error.get('lastErrorTimestamp')
        timestamp = _format_dt(timestamp_raw) or str(timestamp_raw or '')
        if timestamp:
            age = _relative_age(timestamp_raw if isinstance(timestamp_raw, str) else None)
            if age:
                timestamp = '{} ({})'.format(timestamp, age)

        instance_short = _short_id(runtime_error.get('instanceId'))
        if instance_short:
            _labeled('Instance               ', instance_short)
        if state:
            _labeled('State                  ', state)
        if last_error:
            _labeled('Last Error             ', last_error)
        if details:
            _labeled('Last Error Details     ', details)
        if timestamp:
            _labeled('Last Error Timestamp   ', timestamp)

        _out()

    # ---- Section 3: Suggested next steps ----
    # Show actionable next steps when either source found a problem. Config
    # update commands require a flagged built-in check; application logs are
    # useful for both configuration findings and runtime errors.
    if any_issue or show_runtime:
        rg = payload.get('resourceGroup') or '<resource-group>'
        site_name = payload.get('name') or '<site-name>'
        _out()
        _out((Style.WARNING, '▶ Hint:'))
        if any_issue:
            _out('  Update flagged app setting:  az webapp config appsettings set -n {} -g {} '
                 '--settings KEY=VALUE'.format(site_name, rg))
            _out('  Update flagged config:       az webapp config set -n {} -g {} '
                 '--settings KEY=VALUE'.format(site_name, rg))
        _out('  Check application logs:      az webapp log tail -n {} -g {}'.format(site_name, rg))
