"""Own the Azure CLI to CLI Extensions implementation handoff."""


def start_extension_tracker_task(issue_number, view, target, prompt, command, summary):
    """Create or resume the scoped extension tracker and Copilot task."""
    if (
        not isinstance(target, dict)
        or target.get("repo") != "Azure/azure-cli-extensions"
        or not target.get("name")
    ):
        raise ValueError(
            "start_extension_tracker_task requires a CLI Extensions target"
        )
    return start_repository_handoff_task(
        repository=None,
        issue_number=issue_number,
        view=view,
        target=target,
        prompt=prompt,
        command=command,
        summary=summary,
    )
