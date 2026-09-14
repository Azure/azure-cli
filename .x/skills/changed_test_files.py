# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Select changed Azure CLI live-test files."""


def changed_test_files(pr_files):
    """Return unique changed pytest paths outside azure-cli-core."""
    selected = []
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
        if normalized not in seen:
            seen.add(normalized)
            selected.append(normalized)
    return selected
