# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.command_modules.role._msgrpah._graph_client import _get_user_url


def test_get_user_url():
    # userPrincipalName beginning with a $ character
    url = _get_user_url('$AdeleVance@contoso.com')
    assert url == "/users('$AdeleVance@contoso.com')"

    # userPrincipalName with # character (B2B user)
    url = _get_user_url('AdeleVance_adatum.com#EXT#@contoso.com')
    assert url == '/users/AdeleVance_adatum.com%23EXT%23@contoso.com'

    # object ID
    url = _get_user_url('bc04869a-5338-4dc1-95a8-5bc10da06c91')
    assert url == "/users/bc04869a-5338-4dc1-95a8-5bc10da06c91"
