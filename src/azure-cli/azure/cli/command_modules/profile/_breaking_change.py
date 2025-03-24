# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.breaking_change import register_conditional_breaking_change, AzCLIOtherChange

register_conditional_breaking_change(tag='ManagedIdentityUsernameBreakingChange', breaking_change=AzCLIOtherChange(
    'login',
    'Passing the managed identity ID with --username is deprecated and will be removed in 2.73.0. '
    'Use --client-id, --object-id or --resource-id instead.'))
