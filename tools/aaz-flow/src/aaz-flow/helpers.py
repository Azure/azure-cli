# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import asyncio
import os
import shutil
import sys
from pathlib import Path
from typing import Literal

from fastmcp import Context
from models import AAZRequest

paths = {
    "aaz": os.getenv("AAZ_PATH", "/workspaces/aaz"),
    "cli": os.getenv("CLI_PATH", "/workspaces/azure-cli"),
    "cli_extension": os.getenv("CLI_EXTENSION_PATH", "/workspaces/azure-cli-extensions"),
    "swagger_path": os.getenv("SWAGGER_PATH", "/workspaces/azure-rest-api-specs"),
}


def _resolve_python_candidates() -> list[str]:
    """Find available Python executables in order of preference."""
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
    """Find the correct aaz-dev command to use."""
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


async def fetch_available_services():
    """Retrieve available services by parsing local azure-rest-api-specs/specification directory."""
    spec_path = os.path.join(paths["swagger_path"], "specification")
    if not os.path.exists(spec_path):
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


def fetch_tag_and_rp(module_name: str) -> list:
    """Extract tags and resource providers from swagger readme.md file."""
    read_me = os.path.join(
        paths["swagger_path"], "specification", module_name, "resource-manager", "readme.md"
    )
    if not os.path.exists(read_me):
        return []
    
    tags = []
    try:
        with open(read_me, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('### Tag:'):
                    tag = line.split('### Tag:')[1].strip()
                    tags.append(tag)
    except Exception:
        tags = []

    resource_providers = []
    try:
        with open(read_me, 'r') as f:
            lines = f.readlines()
            for idx, line in enumerate(lines):
                if line.strip().startswith('input-file:'):
                    for next_line in lines[idx+1:]:
                        next_line = next_line.strip()
                        if next_line.startswith('-'):
                            path = next_line.lstrip('-').strip()
                            parts = path.split('/')
                            if parts:
                                resource_providers.append(parts[0])
                        elif next_line == "" or next_line.startswith("#"):
                            continue
                        else:
                            break
                    break
    except Exception:
        resource_providers = []

    return [resource_providers, tags]


async def _select_option(ctx: Context, options: list, option_type: str) -> str:
    if len(options) == 1:
        selected = options[0]
        await ctx.info(f"Using single {option_type}: {selected}")
        return selected
    
    choice_prompt = await ctx.sample(
        f"When the user clicks on the Respond button, the user will receive a list of {option_type}s to choose from."
        f"Ask the user in a professional manner to select one {option_type} from the list. "
        "The list is provided when they click on the Respond button so do not give any options in the questions itself."
    )
    
    choice = await ctx.elicit(
        message=choice_prompt.text, 
        response_type=Literal[*options] if options else str
    )
    
    if choice.action != "accept":
        return None
    return choice.data


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
        "When the user clicks on the Respond button, the user will receive a list openapi specification resources to choose from."
        "This list is fetched directly from the Azure REST API Specs repository. "
        "Ask the user in a professional manner to select an openapi specification resource from the list. "
        "The list is provided when they click on the Respond button so do not give them any options in the questions itself. "
        "The result of this option selection will determine which module's code will be generated for Azure CLI."
        "The request to the user should start from Please as the first word."
    )
    extension_choice = await ctx.elicit(
        message=choice_prompt.text, response_type=Literal[tuple(
            common_extensions)]
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


async def _select_option(ctx: Context, options: list, option_type: str) -> str:
    """Helper function to select from options or use single option directly."""
    if len(options) == 1:
        selected = options[0]
        await ctx.info(f"Using single {option_type}: {selected}")
        return selected
    
    choice_prompt = await ctx.sample(
        f"When the user clicks on the Respond button, the user will receive a list of {option_type}s to choose from."
        f"Ask the user in a professional manner to select one {option_type} from the list. "
        "The list is provided when they click on the Respond button so do not give any options in the questions itself."
    )
    
    choice = await ctx.elicit(
        message=choice_prompt.text, 
        response_type=Literal[*options] if options else str
    )
    
    if choice.action != "accept":
        return None
    return choice.data


async def construct_config(ctx: Context, name: str, resource_providers: list, tags: list) -> dict:
    """Construct configuration by selecting resource provider and tag."""
    await ctx.info(f"Found resource providers: {resource_providers}")
    await ctx.info(f"Found tags: {tags}")

    if not resource_providers or not tags:
        await ctx.info("Invalid configuration. Code generation cancelled.")
        return {}

    resource_provider = await _select_option(ctx, resource_providers, "resource provider")
    if resource_provider is None:
        return None

    swagger_tag = await _select_option(ctx, tags, "swagger tag")
    if swagger_tag is None:
        return None

    await ctx.info(
        f"Selected resource provider: {resource_provider}, tag: {swagger_tag}")

    return [resource_provider, swagger_tag]


async def run_command(
    ctx: Context, command: str, step_name: str, progress_start: int, progress_end: int
):
    """Execute a shell command with progress tracking and output logging."""
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
            progress_range, int(
                (lines_count / total_lines_estimate) * progress_range)
        )
        await ctx.report_progress(progress, 100)

    await process.wait()

    if process.returncode != 0:
        raise RuntimeError(f"{step_name} failed: {command}")

    await ctx.report_progress(progress_end, 100)
    await ctx.info(f"az_cli : Completed: {step_name}")


async def execute_commands(ctx: Context, paths: dict, request: AAZRequest):
    """Execute the AAZ development commands for code generation."""
    aaz_dev = _resolve_aaz_dev_prefix()
    await ctx.info(f"az_cli : Using aaz-dev invocation: {aaz_dev}")

    prompt = await ctx.sample(
        "Ask the user to provide a name for the generated module/extension. "
        "To use the default name, they can simply press Cancel."
    )

    module_name_response = await ctx.elicit(prompt.text, response_type=str)
    if module_name_response.action != "accept" or not module_name_response.data:
        await ctx.info("No module name provided. The default name will be used.")
        module_name = request.name
    else:
        module_name = module_name_response.data

    cmd = (
        f"{aaz_dev} cli generate "
        f"-s {request.name} "
        f"-m {module_name}"
    )

    try:
        await run_command(ctx, cmd, "Generate CLI code", 80, 100)
    except Exception as e:
        await ctx.info(f"az_cli : Code generation failed: {str(e)}")
        return f"Code generation failed: {str(e)}"

    return "Azure CLI code generation completed successfully!"


async def run_code_generation(ctx: Context, name: str, paths: dict):
    """Run the complete code generation workflow."""
    resource_providers, tags = fetch_tag_and_rp(name)
    if not resource_providers or not tags:
        return None, "Code generation cancelled."

    resource_provider, swagger_tag = await construct_config(ctx, name, resource_providers, tags)

    request = AAZRequest(
        name=name,
        swagger_module_path=os.path.join(paths['swagger_path'], 'specification', name),
        resource_provider=resource_provider,
        swagger_tag=swagger_tag,
    )

    await execute_commands(ctx, paths, request)
    ctx.generated_module = name

    await ctx.info(f"Code generation completed for extension/module '{name}'.")
    return name, None


async def get_validated_paths(ctx: Context):
    """Get and validate all required paths."""
    paths = await validate_paths(ctx)
    if not paths:
        await ctx.info("Operation cancelled due to invalid paths.")
        return None
    return paths


async def get_module_name(ctx: Context, module_name: str | None = None):
    """Get module name from parameter or user input."""
    if not module_name:
        response = await ctx.elicit(
            "Enter the module/extension name to generate tests for:"
        )
        if response.action != "accept" or not response.data:
            await ctx.info("Operation cancelled due to missing module name.")
            return None
        module_name = response.data
    else:
        await ctx.info(f"Detected generated module: {module_name}")
    ctx.generated_module = module_name
    return module_name
