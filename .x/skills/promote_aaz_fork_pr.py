# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Bind generation-source promotion to Azure CLI."""


def promote_aaz_fork_pr(fork_pr_number, title, body):
    """Promote one validated AAZ fork pull request."""
    return promote_generation_source_fork_pr(
        repository="Azure/azure-cli",
        fork_pr_number=fork_pr_number,
        title=title,
        body=body,
    )
