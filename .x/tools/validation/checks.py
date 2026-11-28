# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Azure CLI validation hooks; loaded only from the job's pinned package."""

import json

from x_engineering_agent.tools.copilot.validation import run_command

_CLI_PACKAGES = ("azure-cli", "azure-cli-core", "azure-cli-telemetry", "azure-cli-testsdk")


def unit_test_scope(repository, root, parts):
    """Directory searched for unit tests of a changed file, or None."""
    if "command_modules" in parts:
        index = parts.index("command_modules")
        return root.joinpath(*parts[:index + 2]) / "tests" if len(parts) > index + 1 else None
    if len(parts) > 1 and parts[0] == "src":
        return root / "src" / parts[1]
    return None


def python_roots(repository, root, tests):
    """PYTHONPATH roots besides the checkout root."""
    return [root / "src" / name for name in _CLI_PACKAGES]


def generation_source_checks(root, changed, deadline):
    """Schema and reference checks for Azure/aaz command models."""
    return {"aaz": _aaz_checks(root, changed, deadline)}


def _aaz_checks(root, changed, deadline):
    import aaz_dev  # noqa: F401 -- installs the tool's documented internal import root.
    from command.model.configuration import CMDClientConfig, CMDConfiguration, XMLSerializer

    groups = set()
    models = 0
    full = False
    for path in changed:
        relative = path.relative_to(root)
        if relative.parts[0] == "Commands":
            if len(relative.parts) > 2 and (root / "Commands" / relative.parts[1]).is_dir():
                groups.add(relative.parts[1])
            else:
                full = True
        if relative.parts[0] != "Resources" or path.suffix not in {".json", ".xml"}:
            continue
        if not path.exists():
            full = True
            continue
        for candidate in (path.with_suffix(".json"), path.with_suffix(".xml")):
            if not candidate.is_file():
                raise ValueError("AAZ resource validation requires both JSON and XML representations")
            model_type = CMDClientConfig if candidate.name.startswith("client") else CMDConfiguration
            model = (model_type(json.loads(candidate.read_text())) if candidate.suffix == ".json"
                     else XMLSerializer.from_xml(model_type, candidate.read_text()))
            model.validate()
            if model_type is CMDConfiguration:
                model.link()
                groups.update(group.name.split()[0] for group in model.command_groups)
            model.reformat()
            model.validate()
            models += 1
    targets = [None] if full or not groups else sorted(groups)
    for target in targets:
        argv = ["aaz-dev", "command-model", "verify", "--aaz-path", str(root)]
        if target is not None:
            if not (root / "Commands" / target).is_dir():
                raise ValueError("AAZ verification target does not exist")
            argv += ["--target", target]
        run_command(argv, root=root, deadline=deadline)
    return {"schema_models": models, "metadata_targets": len(targets), "coverage": "schema_and_reference_consistency"}
