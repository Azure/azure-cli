# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError


def validate_alert_status(namespace):
    lower_status = namespace.status.lower()
    if lower_status not in ['dismiss', 'activate', 'resolve', 'inprogress']:
        raise CLIError('--status can only accept "Dismiss", "Activate", "InProgress" or "Resolve" values')


def validate_auto_provisioning_toggle(namespace):
    lower_toggle = namespace.auto_provision.lower()
    if lower_toggle not in ['on', 'off']:
        raise CLIError('--auto-provision can only accept "on" or "off" values')


def validate_pricing_tier(namespace):
    pricing_tier = namespace.tier.lower()
    if pricing_tier not in ['free', 'standard']:
        raise CLIError('--tier can only accept "standard" or "free" values')


def validate_assessment_status_code(namespace):
    status_code = namespace.status_code.lower()
    if status_code not in ['healthy', 'unhealthy', 'notapplicable']:
        raise CLIError('--status-code can only accept "healthy", "unhealthy" or "notapplicable" values')
