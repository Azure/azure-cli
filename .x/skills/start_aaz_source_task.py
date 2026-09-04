"""Bind durable generation-source task creation to Azure CLI."""


def start_aaz_source_task(issue_number, downstream_pr_url, changed_files, prompt_context):
    """Start the configured AAZ source task for an Azure CLI pull request."""
    return start_generation_source_task(
        repository="Azure/azure-cli",
        issue_number=issue_number,
        downstream_pr_url=downstream_pr_url,
        changed_files=changed_files,
        prompt_context=prompt_context,
    )
