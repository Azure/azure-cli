# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.breaking_change import register_other_breaking_change

register_other_breaking_change(
    'policy assignment identity remove',
    'Removing a user assigned identity will change in a future release of the resource commands. '
    'It will require providing the --mi-user-assigned switch.')
register_other_breaking_change(
    'policy assignment identity assign',
    'Replacing an existing identity will change in a future release of the resource commands. '
    'It will require first removing the existing identity.')
register_other_breaking_change(
    'policy assignment non-compliance-message create',
    'The return value will change in a future release of the resource commands. '
    'It will be the single created message object rather than the full array of message objects.')
register_other_breaking_change(
    'policy assignment non-compliance-message delete',
    'The return value will change in a future release of the resource commands. '
    'It will be empty rather than the full array of remaining message objects.')
register_other_breaking_change(
    'policy assignment non-compliance-message create',
    'The return value will change in a future release of the resource commands. '
    'It will be the single created message object rather than the full array of message objects.')
register_other_breaking_change(
    'policy definition delete',
    'Behavior will change in a future release of the resource commands. '
    'Bypassing the confirmation prompt will require providing the -y switch.')
register_other_breaking_change(
    'policy set-definition delete',
    'Behavior will change in a future release of the resource commands. '
    'Bypassing the confirmation prompt will require providing the -y switch.')
register_other_breaking_change(
    'policy exemption create',
    'Date format will change slightly in a future release of the resource commands. '
    'New format is ISO-8601, e.g. 2025-08-05T00:45:13Z instead of 2025-08-05T00:45:13+00:00.',
    '--expires-on')
register_other_breaking_change(
    'policy exemption update',
    'Date format will change slightly in a future release of the resource commands. '
    'New format is ISO-8601, e.g. 2025-08-05T00:45:13Z instead of 2025-08-05T00:45:13+00:00.',
    '--expires-on')
