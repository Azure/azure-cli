# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def cli_advisor_list_recommendations(client):
    """List all available recommendations for the subscription"""
    return list(client.list())