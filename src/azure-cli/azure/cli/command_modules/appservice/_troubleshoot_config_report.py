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
    total_seconds = int((datetime.now(timezone.utc) - dt).total_seconds())
    if total_seconds < 0:
        age = 'in the future'
    elif total_seconds < 60:
        age = 'just now'
    else:
        minutes = total_seconds // 60
        if minutes < 60:
            age = '{}m ago'.format(minutes)
        else:
            hours, rem_min = divmod(minutes, 60)
            if hours < 24:
                age = '{}h {}m ago'.format(hours, rem_min) if rem_min else '{}h ago'.format(hours)
            else:
                days, rem_hours = divmod(hours, 24)
                age = '{}d {}h ago'.format(days, rem_hours) if rem_hours else '{}d ago'.format(days)
    return age


def _out(*objs):
    print_styled_text(*objs, file=sys.stdout)


def _row(*objs):
    _out(list(objs))


def _labeled(label, value, style=Style.PRIMARY):
    """Emit a labeled value with wrapped lines aligned below the value."""
    text = '' if value is None else str(value)
    term_w = shutil.get_terminal_size(fallback=(120, 40)).columns
    indent = ' ' * len(label)
    lines = textwrap.wrap(text, width=max(20, term_w - len(label))) or [text]
    _row((style, label), (style, lines[0]))
    for continuation in lines[1:]:
        _row((style, indent), (style, continuation))


def _details_level(setting):
    raw = setting.get('DetailsLevel')
    if raw is None:
        raw = setting.get('detailsLevel')
    level = raw.strip().lower() if isinstance(raw, str) else ''
    return level if level in ('info', 'warning', 'error') else 'info'


def _style_for_level(level):
    if level == 'error':
        return Style.ERROR
    if level == 'warning':
        return Style.WARNING
    return Style.SUCCESS


def _get_settings(config_check):
    settings = config_check.get('Settings') or config_check.get('settings') or []
    if not isinstance(settings, list):
        return []
    return [setting for setting in settings if isinstance(setting, dict)]


def _render_snapshot_metadata(payload, config_check):
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
        _labeled('Last Updated: ', _format_dt(written_at_raw) or str(written_at_raw), Style.HIGHLIGHT)


def _render_settings_table(settings):
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
        name = str(setting.get('Setting') or '')
        value = str(setting.get('Value') if setting.get('Value') is not None else '')
        details = str(setting.get('Details') or '')
        prefix = '{s:<{sw}}{v:<{vw}}'.format(s=name, sw=setting_w, v=value, vw=value_w)
        lines = textwrap.wrap(details, width=max(20, term_w - len(prefix))) or [details]
        details_style = _style_for_level(_details_level(setting))
        _row((Style.PRIMARY, prefix), (details_style, lines[0]))
        for continuation in lines[1:]:
            _row((Style.PRIMARY, ' ' * len(prefix)), (details_style, continuation))


def _render_config_checks(payload, config_check, settings):
    if payload.get('configCheck') is not None:
        _render_snapshot_metadata(payload, config_check)
    _out()
    _row((Style.HIGHLIGHT, '═══ BUILT-IN CHECKS ' + '═' * 55))
    _out()
    if payload.get('configCheck') is None:
        if payload.get('configCheckStatus') == 404:
            message = payload.get('configCheckMessage') or (
                'Configuration check feature is currently disabled. Please try again later.')
            _row((Style.WARNING, message))
        else:
            _row((Style.WARNING,
                  'Failed to retrieve built-in configuration checks. Please try again. '
                  'If the issue persists, restart the application (\'az webapp restart\') and confirm the SCM (Kudu) '
                  'is running and reachable.'))
        return

    if not settings:
        _row((Style.WARNING, 'No built-in configuration checks reported.'))
    else:
        _render_settings_table(settings)


def _render_runtime_error(runtime_error):
    _out()
    _out()
    _row((Style.HIGHLIGHT, '═══ SITE RUNTIME ERROR RECOMMENDATION ' + '═' * 37))
    _out()
    timestamp_raw = runtime_error.get('lastErrorTimestamp')
    timestamp = _format_dt(timestamp_raw) or str(timestamp_raw or '')
    age = _relative_age(timestamp_raw) if timestamp else None
    if age:
        timestamp = '{} ({})'.format(timestamp, age)

    fields = [
        ('Instance               ', _short_id(runtime_error.get('instanceId'))),
        ('State                  ', runtime_error.get('state')),
        ('Last Error             ', runtime_error.get('lastError')),
        ('Last Error Details     ', runtime_error.get('lastErrorDetails')),
        ('Last Error Timestamp   ', timestamp),
    ]
    for label, value in fields:
        if value:
            _labeled(label, value)
    _out()


def _render_hints(payload, any_issue):
    resource_group = payload.get('resourceGroup') or '<resource-group>'
    site_name = payload.get('name') or '<site-name>'
    _out()
    _out((Style.WARNING, '▶ Hint:'))
    if any_issue:
        _out('  Update flagged app setting:  az webapp config appsettings set -n {} -g {} '
             '--settings KEY=VALUE'.format(site_name, resource_group))
        _out('  Update flagged config:       az webapp config set -n {} -g {} '
             '--settings KEY=VALUE'.format(site_name, resource_group))
    _out('  Check application logs:      az webapp log tail -n {} -g {}'.format(
        site_name, resource_group))


def render_report(payload):
    """Print built-in checks, a recent runtime recommendation, and hints."""
    config_check = payload.get('configCheck') or {}
    settings = _get_settings(config_check)
    runtime_error = payload.get('runtimeError')
    show_runtime = bool(runtime_error and runtime_error.get('isRecent'))
    any_issue = any(_details_level(setting) in ('warning', 'error') for setting in settings)

    _render_config_checks(payload, config_check, settings)
    if show_runtime:
        _render_runtime_error(runtime_error)
    if any_issue or show_runtime:
        _render_hints(payload, any_issue)
