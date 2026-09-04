"""Bind generation-source candidate discovery to Azure CLI."""


def find_aaz_fork_prs_ready_for_promotion():
    """Find completed AAZ fork pull requests ready for promotion."""
    return find_generation_source_fork_prs_ready_for_promotion(
        repository="Azure/azure-cli",
    )
