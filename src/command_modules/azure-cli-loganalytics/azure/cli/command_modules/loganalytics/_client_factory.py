# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def loganalytics_data_plane_client(cli_ctx, _):
    """Initialize Log Analytics data client for use with CLI."""
    from azure.loganalytics import LogAnalyticsDataClient
    from azure.cli.core._profile import Profile
    profile = Profile(cli_ctx=cli_ctx)
    cred, _, _ = profile.get_login_credentials(
        resource=cli_ctx.cloud.endpoints.log_analytics_resource_id)
    return LogAnalyticsDataClient(cred)
