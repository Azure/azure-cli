"""Bind generation-source promotion to Azure CLI."""


def promote_aaz_fork_pr(fork_pr_number, title, body):
    """Promote one validated AAZ fork pull request."""
    return promote_generation_source_fork_pr(
        repository=None,
        fork_pr_number=fork_pr_number,
        title=title,
        body=body,
    )
