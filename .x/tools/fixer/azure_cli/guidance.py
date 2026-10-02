# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Repository-owned Codegen execution guidance."""


def _codegen_execution_guidance(kind, safe_component):
    module = safe_component or "<module>"
    target_flag = (
        "--cli-extension-path <azure-cli-extensions>"
        if kind == "cli-ext"
        else "--cli-path <azure-cli>"
    )
    return (
        "### Mandatory Codegen execution protocol\n\n"
        "Before editing implementation files, determine whether the "
        f"affected `{module}` command is AAZ-generated. Files under "
        "`aaz/<profile>/` are generated output and must never be patched "
        "directly, including by an AI agent. Check out `Azure/aaz` beside "
        "`Azure/azure-rest-api-specs`, `Azure/aaz-dev-tools`, and the "
        "downstream repository. API-schema defects start in the "
        "specification; command naming, grouping, arguments, API-version "
        "selection, help, and examples belong in the durable `Azure/aaz` "
        "command model; non-modelable client behavior belongs in a "
        "handwritten subclass or wrapper in `custom.py`, registered from "
        "`commands.py`. X Engineering Agent creates and promotes the corresponding "
        "durable `Azure/aaz` source pull request before it promotes "
        "downstream generated output.\n\n"
        "Follow the Azure CLI repository's "
        "[Codegen workflow]"
        "(https://github.com/Azure/azure-cli/blob/dev/"
        "doc/hands_on_codespace.md) and the "
        "[aaz-dev setup documentation]"
        "(https://github.com/Azure/aaz-dev-tools/blob/dev/README.md). "
        "Set up the checked-out repositories with `azdev setup`. Use "
        "`generate` only when importing or redesigning command models from "
        "Swagger/TypeSpec. For an existing module whose durable "
        "`Azure/aaz` model has been updated, render that model with "
        "`regenerate`:\n\n"
        "```bash\n"
        f"aaz-dev cli regenerate --name {module} {target_flag}\n"
        "\n"
        "# New/imported command model only:\n"
        f"aaz-dev cli generate --spec <specification-name> "
        f"--module {module}\n"
        "```\n\n"
        "You MUST actually run the generator; do not merely describe it "
        "or imitate its output. If the AAZ/specification checkout, local "
        "source change, credentials, or generator is unavailable, stop "
        "and report the blocker instead of editing generated files. "
        "Inspect `_aaz_info` provenance and the complete regenerated diff, "
        "then run focused `azdev style`, `azdev linter`, and `azdev test` "
        "validation. For an extension, also update its version and "
        "`HISTORY.rst`, preserve `azext_metadata.json` compatibility, and "
        "let release automation update `src/index.json`."
    )
