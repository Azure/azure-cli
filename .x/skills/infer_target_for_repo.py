# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Infer an Azure CLI module or extension from trusted repository structure."""


def infer_target_for_repo(repo_full_name, text, pr_files):
    """Resolve a sanitized issue or PR diff to a live CLI target."""
    if repo_full_name != "Azure/azure-cli":
        raise ValueError("infer_target_for_repo is restricted to Azure/azure-cli")

    modules = list_repository_directories(
        source_repository="Azure/azure-cli",
    )
    extensions = list_repository_directories(
        source_repository="Azure/azure-cli-extensions",
    )

    def normalize(value):
        return "".join(
            character
            for character in str(value or "").casefold()
            if character.isalnum()
        )

    def resolve(candidate):
        candidate_normalized = normalize(candidate)
        for extension in extensions:
            if normalize(extension) == candidate_normalized:
                return {
                    "kind": "extension",
                    "name": extension,
                    "repo": "Azure/azure-cli-extensions",
                }
        for module in modules:
            if normalize(module) == candidate_normalized:
                return {
                    "kind": "module",
                    "name": module,
                    "repo": "Azure/azure-cli",
                }
        return None

    scores = {}
    for path in pr_files or []:
        parts = str(path).replace("\\", "/").split("/")
        if "command_modules" in parts:
            index = parts.index("command_modules")
            if index + 1 < len(parts):
                candidate = parts[index + 1]
                scores[candidate] = scores.get(candidate, 0) + 10
        elif len(parts) > 1 and parts[0].casefold() == "src":
            candidate = parts[1]
            scores[candidate] = scores.get(candidate, 0) + 10
    if pr_files:
        for candidate in sorted(scores, key=lambda item: (-scores[item], item)):
            target = resolve(candidate)
            if target is not None:
                return target
        return {"kind": "none", "name": None, "repo": None}

    cleaned = "".join(
        character if character.isalnum() or character in "-_./" else " "
        for character in str(text or "").casefold()
    )
    words = cleaned.split()
    for index, word in enumerate(words):
        if word == "az" and index + 1 < len(words):
            candidate = words[index + 1]
            scores[candidate] = scores.get(candidate, 0) + 5
        if word.startswith("src/"):
            parts = word.split("/")
            if len(parts) > 1:
                candidate = parts[1]
                scores[candidate] = scores.get(candidate, 0) + 3
        if "command_modules/" in word:
            candidate = word.split("command_modules/", 1)[1].split("/", 1)[0]
            scores[candidate] = scores.get(candidate, 0) + 3
    for candidate in sorted(scores, key=lambda item: (-scores[item], item)):
        target = resolve(candidate)
        if target is not None:
            return target
    return {"kind": "unknown", "name": None, "repo": None}
