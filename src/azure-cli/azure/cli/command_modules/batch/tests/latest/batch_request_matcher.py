# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import re

import isodate

_SUBSCRIPTION_ID = re.compile(r'/subscriptions/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}(?=/)',
                              re.IGNORECASE)
_MISSING = object()
_NO_BODY = object()
_NOT_JSON = object()


def register_batch_body_matcher(vcr):
    """In playback, a Batch request only matches a recorded request with the same JSON body."""
    vcr.register_matcher('batch_body', batch_body)
    vcr.match_on = tuple(vcr.match_on) + ('batch_body',)


def batch_body(r1, r2):
    """vcrpy matcher for the current request (r1) and a recorded one (r2). Requests to other services always match.

    Raises AssertionError with the JSON paths that differ, which vcrpy shows when no recorded request matches.
    """
    if not (_is_batch_request(r1) and _is_batch_request(r2)):
        return True
    now, recorded = _load_json(r1.body), _load_json(r2.body)
    if now is _NOT_JSON or recorded is _NOT_JSON:
        return True
    differences = list(_differences(recorded, now, ''))
    if differences:
        raise AssertionError('The request body differs from the recording:\n' + '\n'.join(
            f'  {path}: recorded {_show(old)}, now {_show(new)}' for path, old, new in differences))
    return True


def _is_batch_request(request):
    return (request.host or '').lower().endswith('.batch.azure.com') or \
        '/providers/microsoft.batch/' in request.path.lower()


def _load_json(body):
    """The body as JSON, _NO_BODY or _NOT_JSON."""
    if body in (None, b'', ''):
        return _NO_BODY
    if not isinstance(body, (bytes, str)):
        return _NOT_JSON
    try:
        return json.loads(body)
    except ValueError:
        return _NOT_JSON


def _differences(recorded, now, path):
    """Yield (path, recorded value, current value) for each JSON path where the values differ."""
    if isinstance(recorded, dict) and isinstance(now, dict):
        for key in sorted(set(recorded) | set(now)):
            yield from _differences(recorded.get(key, _MISSING), now.get(key, _MISSING),
                                    f'{path}.{key}' if path else key)
    elif isinstance(recorded, list) and isinstance(now, list):
        for index in range(max(len(recorded), len(now))):
            yield from _differences(recorded[index] if index < len(recorded) else _MISSING,
                                    now[index] if index < len(now) else _MISSING, f'{path}[{index}]')
    elif not _same_value(recorded, now):
        yield path or '<body>', recorded, now


def _same_value(recorded, now):
    if type(recorded) is not type(now):
        return False
    if recorded == now:
        return True
    if not isinstance(now, str):
        return False
    # Recordings hold a placeholder subscription ID, and a duration can be written in several ways
    if _SUBSCRIPTION_ID.sub('/subscriptions/<id>', recorded) == _SUBSCRIPTION_ID.sub('/subscriptions/<id>', now):
        return True
    try:
        return isodate.parse_duration(recorded) == isodate.parse_duration(now)
    except ValueError:  # not durations
        return False


def _show(value):
    if value is _MISSING:
        return '<missing>'
    return '<no body>' if value is _NO_BODY else json.dumps(value)
