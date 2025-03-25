# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.breaking_change import register_output_breaking_change

register_output_breaking_change(command_name='acr login',
                                description='Exit code will be 1 if command fails for docker login')
