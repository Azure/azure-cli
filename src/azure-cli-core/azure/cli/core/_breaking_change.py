# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

from azure.cli.core.breaking_change import AzCLIOtherChange, register_conditional_breaking_change

register_conditional_breaking_change(
    tag='CloudProfilesDeprecate',
    breaking_change=AzCLIOtherChange(
        cmd='',
        message="Starting from 2.73.0, the azure stack profiles ('2017-03-09-profile', '2018-03-01-hybrid', '2019-03-01-hybrid', '2020-09-01-hybrid') will be deprecated. Please use the 'latest' profile or the CLI 2.66.* (LTS) version instead."
    )
)
