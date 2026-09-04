"""Bind promoted generation-source lookup to Azure CLI."""


def find_promoted_aaz_source_pr(issue_number):
    """Find the promoted AAZ source pull request for an Agent issue."""
    return find_promoted_generation_source_pr(
        repository="Azure/azure-cli",
        issue_number=issue_number,
    )
