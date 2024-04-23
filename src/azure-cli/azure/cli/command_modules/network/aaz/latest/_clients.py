# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.core.aaz import AAZClientConfiguration, register_client
from azure.cli.core.aaz._client import AAZMgmtClient


@register_client("NonRetryableClient")
class AAZNonRetryableClient(AAZMgmtClient):
    @classmethod
    def _build_configuration(cls, ctx, credential, **kwargs):
        from azure.cli.core.auth.util import resource_to_scopes
        from azure.core.pipeline.policies import RetryPolicy

        retry_policy = RetryPolicy(**kwargs)
        retry_policy._retry_on_status_codes.discard(429)
        kwargs["retry_policy"] = retry_policy

        return AAZClientConfiguration(
            credential=credential,
            credential_scopes=resource_to_scopes(ctx.cli_ctx.cloud.endpoints.active_directory_resource_id),
            **kwargs
        )
