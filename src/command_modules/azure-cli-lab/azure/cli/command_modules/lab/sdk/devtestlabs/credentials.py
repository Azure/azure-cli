# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# coding: utf-8
# pylint: skip-file
from msrest.authentication import (
    BasicAuthentication,
    BasicTokenAuthentication,
    OAuthTokenAuthentication)

from msrestazure.azure_active_directory import (
    InteractiveCredentials,
    ServicePrincipalCredentials,
    UserPassCredentials)
