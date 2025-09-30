# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import asyncio
from pathlib import Path
from typing import Literal
from fastmcp import Context
import os
import shutil
import sys
from models import AAZRequest

paths = {
    "aaz": os.getenv("AAZ_PATH", "/workspaces/aaz"),
    "cli": os.getenv("CLI_PATH", "/workspaces/azure-cli"),
    "cli_extension": os.getenv(
        "CLI_EXTENSION_PATH", "/workspaces/azure-cli-extensions"
    ),
    "swagger_path": os.getenv("SWAGGER_PATH", "/workspaces/azure-rest-api-specs"),
}


async def fetch_available_services():
    """Retrieve available services by parsing local azure-rest-api-specs/specification directory"""
    spec_path = os.path.join(paths["swagger_path"], "specification")
    if not os.path.exists(spec_path):
        # Fallback to common services if local path is missing
        return ["storage", "compute", "network", "keyvault", "monitor"]

    try:
        directories = [
            d
            for d in os.listdir(spec_path)
            if os.path.isdir(os.path.join(spec_path, d))
        ]
        directories.sort()
        return directories
    except Exception:
        return ["storage", "compute", "network", "keyvault", "monitor"]


async def validate_paths(ctx: Context) -> dict:
    """Validate and get correct paths for required directories."""

    await ctx.info("az_cli : Validating local paths...")
    await ctx.report_progress(progress=5, total=100)

    combined_check = await ctx.sample(
        "Ask the user to confirm if the detected paths for AAZ, Azure CLI, Azure CLI Extensions and Swagger specs are correct. The detected paths are as follows:\n"
        f"- AAZ path: `{paths['aaz']}`\n"
        f"- Azure CLI path: `{paths['cli']}`\n"
        f"- Azure CLI Extensions path: `{paths['cli_extension']}`\n"
        f"- Swagger specifications path: `{paths['swagger_path']}`\n"
        "If any path is incorrect, ask the user to answer with 'no'."
    )

    check_result = await ctx.elicit(
        message=combined_check.text, response_type=Literal["yes", "no"]
    )

    if check_result.action != "accept":
        return None

    if check_result.data != "yes":
        for i, (key, path) in enumerate(paths.items(), 1):
            progress = 5 + (i * 5)
            await ctx.report_progress(progress=progress, total=100)

            display_name = key.replace("_", " ")
            phrased_question = await ctx.sample(
                f"Ask the user to confirm the path for {display_name} directory: {path}. Use `` around the path when displaying it."
            )
            check_result = await ctx.elicit(
                message=phrased_question.text, response_type=Literal["yes", "no"]
            )

            if check_result.action != "accept":
                return None

            if check_result.data == "no":
                elicit_question = await ctx.sample(
                    f"Ask the user to provide the correct path for the {display_name} directory."
                )
                new_path_result = await ctx.elicit(
                    message=elicit_question.text, response_type=str
                )
                if new_path_result.action != "accept":
                    return None
                paths[key] = new_path_result.data.strip('"')
                await ctx.info(f"az_cli : Updated {display_name} path to: {paths[key]}")

    await ctx.info("az_cli : Verifying path existence...")
    await ctx.report_progress(progress=30, total=100)

    for key, path in paths.items():
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"{key.replace('_', ' ')} path does not exist: {path}"
            )

    await ctx.info("az_cli : Path validation completed.")
    await ctx.report_progress(progress=35, total=100)
    return paths


async def get_name(ctx: Context) -> str:
    """Get the extension or module name from user."""
    await ctx.info("az_cli : Fetching available services...")
    common_extensions = await fetch_available_services()
    await ctx.report_progress(progress=40, total=100)

    choice_prompt = await ctx.sample(
        "When the user clicks on the Respond button, the user will receive a list of Azure CLI modules and extensions to choose from."
        "This list is fetched directly from the Azure REST API Specs repository. "
        "Ask the user in a professional manner to select a module/extension from the list. "
        "The list is provided when they click on the Respond button so do not give them any options in the questions itself. "
        "The result of this option selection will determine which module's code will be generated for Azure CLI."
    )
    extension_choice = await ctx.elicit(
        message=choice_prompt.text, response_type=Literal[tuple(common_extensions)]
    )

    if extension_choice.action != "accept":
        return None

    if extension_choice.data == "other":
        custom_extension = await ctx.elicit(
            "Enter custom extension/module name:", response_type=str
        )
        if custom_extension.action != "accept":
            return None
        return custom_extension.data

    return extension_choice.data


async def get_swagger_config(
    ctx: Context, paths: dict, service_name: str = None
) -> dict:
    """Get Swagger configuration details from user."""
    await ctx.info("az_cli : Browsing Swagger specifications...")
    await ctx.report_progress(progress=60, total=100)

    spec_result = await browse_specs(
        ctx,
        os.path.join(
            paths["swagger_path"], "specification", service_name, "resource-manager"
        ),
    )
    if not spec_result:
        return None
    else:
        return spec_result


async def browse_specs(ctx: Context, base_path: str):
    """Interactive browser for Swagger specifications with clean labels and correct metadata extraction."""
    await ctx.info("az_cli : Starting specification browser...")

    current_path = base_path
    navigation_count = 0

    while True:
        navigation_count += 1
        await ctx.info(f"az_cli : Browsing {current_path} (step {navigation_count})")

        try:
            entries = sorted(os.listdir(current_path))
        except FileNotFoundError:
            await ctx.info(f"az_cli : Directory not found: {current_path}")
            return None

        dirs = [e for e in entries if os.path.isdir(os.path.join(current_path, e))]
        files = [
            e
            for e in entries
            if os.path.isfile(os.path.join(current_path, e))
            and e.endswith((".json", ".yaml", ".yml"))
        ]

        labels = [".."] + [f"> {d}" for d in dirs] + files
        mapping = dict(zip(labels, [".."] + dirs + files))

        choice = await ctx.elicit(
            message="Click on the respond button to browse through the sub-folders of the chosen service and select the appropriate spec file.",
            response_type=Literal[tuple(labels)],
        )

        if choice.action != "accept":
            await ctx.info("az_cli : Specification browsing cancelled")
            return None

        selected = mapping[choice.data]

        if selected == "..":
            current_path = os.path.dirname(current_path)
            await ctx.info(f"az_cli : Moved up to: {current_path}")
        elif selected in dirs:
            current_path = os.path.join(current_path, selected)
            await ctx.info(f"az_cli : Entered directory: {selected}")
        else:
            selected_file_path = os.path.join(current_path, selected)
            await ctx.info(f"az_cli : Selected spec file: {selected_file_path}")

            rel_path = os.path.relpath(selected_file_path, base_path)
            parts = rel_path.split(os.sep)

            resource_provider = parts[0] if len(parts) > 0 else None
            release = parts[2] if len(parts) > 2 else None
            swagger_tag = f"package-{release}" if release else None

            result = {
                "file": os.path.dirname(base_path),
                "resource_provider": resource_provider,
                "release": release,
                "swagger_tag": swagger_tag,
            }

            await ctx.info(
                f"az_cli : Extracted: Resource Provider={resource_provider}, Release={release}, Tag={swagger_tag}"
            )
            return result


async def run_command(
    ctx: Context, command: str, step_name: str, progress_start: int, progress_end: int
):
    await ctx.info(f"az_cli : Starting: {step_name}")
    process = await asyncio.create_subprocess_shell(
        command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
    )

    progress_range = progress_end - progress_start
    lines_count = 0
    total_lines_estimate = 50

    while True:
        line = await process.stdout.readline()
        if not line:
            if process.returncode is not None:
                break
            await asyncio.sleep(0.1)
            continue
        lines_count += 1
        await ctx.info(f"az_cli : {line.decode().rstrip()}")
        progress = progress_start + min(
            progress_range, int((lines_count / total_lines_estimate) * progress_range)
        )
        await ctx.report_progress(progress, 100)

    await process.wait()

    if process.returncode != 0:
        raise RuntimeError(f"{step_name} failed: {command}")

    await ctx.report_progress(progress_end, 100)
    await ctx.info(f"az_cli : Completed: {step_name}")


def _resolve_python_candidates() -> list[str]:
    candidates = []
    venv = os.environ.get("VIRTUAL_ENV")
    if venv:
        candidates.append(str(Path(venv) / "bin" / "python"))
    ws_venv_python = Path("/workspaces/.venv/bin/python")
    if ws_venv_python.exists():
        candidates.append(str(ws_venv_python))
    if sys.executable:
        candidates.append(sys.executable)
    for name in ("python3", "python"):
        p = shutil.which(name)
        if p:
            candidates.append(p)
    deduped = []
    seen = set()
    for c in candidates:
        if c not in seen:
            deduped.append(c)
            seen.add(c)
    return deduped


def _resolve_aaz_dev_prefix() -> str:
    for py in _resolve_python_candidates():
        try:
            import subprocess

            code = (
                "import importlib.util, sys; "
                "spec = importlib.util.find_spec('aaz_dev.__main__'); "
                "sys.exit(0 if spec else 1)"
            )
            res = subprocess.run(
                [py, "-c", code],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            if res.returncode == 0:
                return f"{py} -m aaz_dev"
        except Exception:
            pass
    for maybe in [
        "/workspaces/.venv/bin/aaz-dev",
        (
            str(Path(os.environ.get("VIRTUAL_ENV", "")) / "bin" / "aaz-dev")
            if os.environ.get("VIRTUAL_ENV")
            else None
        ),
        shutil.which("aaz-dev"),
    ]:
        if maybe and os.path.exists(maybe):
            return maybe
    return "aaz-dev"


async def execute_commands(ctx: Context, paths: dict, request: AAZRequest):
    aaz_dev = _resolve_aaz_dev_prefix()
    await ctx.info(f"az_cli : Using aaz-dev invocation: {aaz_dev}")

    cmd1 = (
        f"{aaz_dev} command-model generate-from-swagger "
        f"-a {paths['aaz']} "
        f"--sm {request.swagger_module_path} "
        f"-m {request.name} "
        f"--rp {request.resource_provider} "
        f"--swagger-tag {request.swagger_tag}"
    )

    cmd2 = (
        f"{aaz_dev} cli generate-by-swagger-tag "
        f"-a {paths['aaz']} "
        f"-e {paths['cli_extension']} "
        f"--name {request.name} "
        f"--sm {request.swagger_module_path} "
        f"--rp {request.resource_provider} "
        f"--tag {request.swagger_tag} "
        f"--profile latest"
    )

    try:
        await run_command(ctx, cmd1, "Generate command model from Swagger", 50, 80)
        await run_command(ctx, cmd2, "Generate CLI from Swagger tag", 80, 100)
    except Exception as e:
        await ctx.info(f"az_cli : Code generation failed: {str(e)}")
        return f"Code generation failed: {str(e)}"

    return "Azure CLI code generation completed successfully!"
