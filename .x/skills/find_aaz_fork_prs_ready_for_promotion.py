# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Bind generation-source candidate discovery to Azure CLI."""


def find_aaz_fork_prs_ready_for_promotion():
    """Find completed AAZ fork pull requests ready for promotion."""
    return find_generation_source_fork_prs_ready_for_promotion(
        repository="Azure/azure-cli",
    )
