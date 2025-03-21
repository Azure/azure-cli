# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

from azure.cli.core.breaking_change import AzCLIOtherChange, register_conditional_breaking_change

register_conditional_breaking_change(tag='CloudRegisterOutputBreakingChange',
                                     breaking_change=AzCLIOtherChange(cmd='cloud register',
                                                                      message='Starting from 2.73.0, no gallery endpoint will be returned if using endpoint discovery with --endpoint-resource-manager. Please manually set it with --endpoint-gallery.')
                                     )

register_conditional_breaking_change(tag='CloudUpdateOutputBreakingChange',
                                     breaking_change=AzCLIOtherChange(cmd='cloud update',
                                                                      message='Starting from 2.73.0, no gallery endpoint will be returned if using endpoint discovery with --endpoint-resource-manager. Please manually set it with --endpoint-gallery.')
                                     )
