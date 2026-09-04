"""Select changed Azure CLI pytest modules."""


def changed_test_files(pr_files):
    """Return unique changed test filename stems outside azure-cli-core."""
    stems = []
    seen = set()
    for path in pr_files or []:
        normalized = str(path).replace("\\", "/")
        lowered = normalized.casefold()
        name = normalized.rsplit("/", 1)[-1]
        if (
            "/tests/" not in f"/{lowered}"
            or not name.casefold().startswith("test_")
            or not name.casefold().endswith(".py")
            or "azure-cli-core" in lowered.split("/")
        ):
            continue
        stem = name[:-3]
        if stem not in seen:
            seen.add(stem)
            stems.append(stem)
    return stems
