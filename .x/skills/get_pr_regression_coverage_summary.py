"""Evaluate Azure CLI command-module regression coverage."""


def get_pr_regression_coverage_summary(pr_number):
    """Find changed command modules without focused tests or recordings."""
    changes = get_pr_file_changes(
        owner=None,
        repo=None,
        pr_number=pr_number,
    )
    files = [
        item.get("filename")
        for item in changes
        if isinstance(item, dict) and item.get("filename")
    ]
    root = "src/azure-cli/azure/cli/command_modules/"
    production_files = []
    modules = set()
    for path in files:
        normalized = str(path).replace("\\", "/")
        name = normalized.rsplit("/", 1)[-1]
        if (
            normalized.startswith(root)
            and normalized.endswith(".py")
            and "/tests/" not in normalized
            and name not in {"__init__.py", "_help.py"}
        ):
            production_files.append(normalized)
            remainder = normalized[len(root):]
            module = remainder.split("/", 1)[0].split(".", 1)[0].casefold()
            if module:
                modules.add(module)

    test_files = []
    recording_files = []
    covered = set()
    for path in files:
        normalized = str(path).replace("\\", "/")
        if not normalized.startswith(root) or "/tests/" not in normalized:
            continue
        module = (
            normalized[len(root):]
            .split("/", 1)[0]
            .split(".", 1)[0]
            .casefold()
        )
        if module not in modules:
            continue
        name = normalized.rsplit("/", 1)[-1]
        if name.casefold().startswith("test_") and name.casefold().endswith(".py"):
            test_files.append(normalized)
            covered.add(module)
        if "/recordings/" in normalized:
            recording_files.append(normalized)
            covered.add(module)

    uncovered = sorted(modules - covered)
    return {
        "applicable": bool(production_files),
        "gap": bool(uncovered),
        "modules": sorted(modules),
        "uncovered_modules": uncovered,
        "production_files": production_files,
        "test_files": test_files,
        "recording_files": recording_files,
    }
