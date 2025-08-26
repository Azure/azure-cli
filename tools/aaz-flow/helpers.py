import asyncio
from pathlib import Path
import sys
from typing import Literal
from fastmcp import Context
import requests
import os
import subprocess as sp
from models import AAZRequest

paths = {
    "aaz": os.getenv("AAZ_PATH", "/workspaces-src/aaz"),
    "cli": "/workspaces/azure-cli",
    "cli_extension": os.getenv("CLI_EXTENSION_PATH", "/workspaces-src/azure-cli-extensions"),
    "swagger_path": os.getenv("SWAGGER_PATH", "/workspaces-src/azure-rest-api-specs")
}

async def fetch_available_services():
    """Fetch available services from azure-rest-api-specs repository."""
    url = "https://api.github.com/repos/a0x1ab/azure-rest-api-specs/contents/specification"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.RequestException:
        return ["storage", "compute", "network", "keyvault", "monitor"]

    directories = [item['name'] for item in response.json() if item['type'] == 'dir']
    directories.sort()
    return directories

async def validate_paths(ctx: Context) -> dict:
    """Validate and get correct paths for required directories."""

    await ctx.info("az_cli : Validating local paths...")
    await ctx.report_progress(progress=5, total=100)

    for i, (key, path) in enumerate(paths.items(), 1):
        progress = 5 + (i * 5)
        await ctx.report_progress(progress=progress, total=100)

        display_name = key.replace('_', ' ')
        phrased_question = await ctx.sample(
            f"Ask the user to confirm the path for {display_name} directory: {path}. Use `` around the path when displaying it."
        )
        check_result = await ctx.elicit(
            message=phrased_question.text,
            response_type=Literal["yes", "no"]
        )

        if check_result.action == "reject":
            return None

        if check_result.data == "no":
            elicit_question = await ctx.sample(
                f"Ask the user to provide the correct path for the {display_name} directory."
            )
            new_path_result = await ctx.elicit(
                message=elicit_question.text,
                response_type=str
            )
            if new_path_result.action != "accept":
                return None
            paths[key] = new_path_result.data.strip('"')
            await ctx.info(f"az_cli : Updated {display_name} path to: {paths[key]}")

    await ctx.info("az_cli : Verifying path existence...")
    await ctx.report_progress(progress=30, total=100)

    for key, path in paths.items():
        if not os.path.exists(path):
            raise FileNotFoundError(f"{key.replace('_', ' ')} path does not exist: {path}")

    await ctx.info("az_cli : Path validation completed.")
    await ctx.report_progress(progress=25, total=100)
    return paths

async def get_extension_name(ctx: Context) -> str:
    """Get the extension or module name from user."""
    await ctx.info("az_cli : Fetching available services...")
    common_extensions = await fetch_available_services()
    await ctx.report_progress(progress=40, total=100)

    choice_prompt = await ctx.sample(
        "When the user clicks on the Respond button, the user will receive a list of Azure CLI modules and extensions to choose from." \
        "This list is fetched directly from the Azure REST API Specs repository. " \
        "Ask the user in a professional manner to select a module/extension from the list. " \
        "The list is provided when they click on the Respond button so do not give them any options in the questions itself. " \
        "The result of this option selection will determine which module's code will be generated using AAZ."
    )
    extension_choice = await ctx.elicit(
        message=choice_prompt.text,
        response_type=Literal[tuple(common_extensions)]
    )

    if extension_choice.action != "accept":
        return None

    if extension_choice.data == "other":
        custom_extension = await ctx.elicit(
            "Enter custom extension/module name:",
            response_type=str
        )
        if custom_extension.action != "accept":
            return None
        return custom_extension.data

    return extension_choice.data

async def get_swagger_config(ctx: Context, paths: dict, service_name: str = None) -> dict:
    """Get Swagger configuration details from user."""
    await ctx.info("az_cli : Browsing Swagger specifications...")
    await ctx.report_progress(progress=60, total=100)

    spec_result = await browse_specs(ctx, os.path.join(paths["swagger_path"], "specification", service_name, "resource-manager"))
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
        files = [e for e in entries if os.path.isfile(os.path.join(current_path, e)) and e.endswith((".json", ".yaml", ".yml"))]

        # Labels shown to the user vs actual values
        labels = [".."] + [f"> {d}" for d in dirs] + files
        mapping = dict(zip(labels, [".."] + dirs + files))

        choice = await ctx.elicit(
            message="Click on the respond button to browse through the sub-folders of the chosen service and select the appropriate spec file.",
            response_type=Literal[tuple(labels)]
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
            # A spec file was chosen
            selected_file_path = os.path.join(current_path, selected)
            await ctx.info(f"az_cli : Selected spec file: {selected_file_path}")

            # Relative path for extracting metadata
            rel_path = os.path.relpath(selected_file_path, base_path)
            parts = rel_path.split(os.sep)

            resource_provider = parts[0] if len(parts) > 0 else None
            release = parts[2] if len(parts) > 2 else None
            swagger_tag = f"package-{release}" if release else None

            result = {
                "file": os.path.dirname(base_path),
                "resource_provider": resource_provider,
                "release": release,
                "swagger_tag": swagger_tag
            }

            await ctx.info(
                f"az_cli : Extracted: Resource Provider={resource_provider}, Release={release}, Tag={swagger_tag}"
            )
            return result

async def run_command(ctx: Context, command: str, step_name: str, progress_start: int, progress_end: int):
    await ctx.info(f"az_cli : Starting: {step_name}")
    process = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT
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
        progress = progress_start + min(progress_range, int((lines_count / total_lines_estimate) * progress_range))
        await ctx.report_progress(progress, 100)

    await process.wait()

    if process.returncode != 0:
        raise RuntimeError(f"{step_name} failed: {command}")

    await ctx.report_progress(progress_end, 100)
    await ctx.info(f"az_cli : Completed: {step_name}")

async def execute_commands(ctx: Context, paths: dict, request: AAZRequest):
    cmd1 = (
        f"aaz-dev command-model generate-from-swagger "
        f"-a {paths['aaz']} "
        f"--sm {request.swagger_module_path} "
        f"-m {request.extension_or_module_name} "
        f"--rp {request.resource_provider} "
        f"--swagger-tag {request.swagger_tag}"
    )

    cmd2 = (
        f"aaz-dev cli generate-by-swagger-tag "
        f"--aaz-path {paths['aaz']} "
        f"--cli-path {paths['cli']} "
        f"--cli-extension-path {paths['cli_extension']} "
        f"--extension-or-module-name {request.extension_or_module_name} "
        f"--swagger-module-path {request.swagger_module_path} "
        f"--resource-provider {request.resource_provider} "
        f"--swagger-tag {request.swagger_tag} "
        f"--profile latest"
    )

    try:
        await run_command(ctx, cmd1, "Generate command model from Swagger", 50, 80)
        await run_command(ctx, cmd2, "Generate CLI from Swagger tag", 80, 100)
    except Exception as e:
        await ctx.info(f"az_cli : Code generation failed: {str(e)}")
        return f"Code generation failed: {str(e)}"

    return "Azure CLI code generation completed successfully!"

async def generate_tests(ctx: "Context"):
    await ctx.info("Starting test generation workflow.")

    module_name = getattr(ctx, "generated_module", None)
    if not module_name:
        response = await ctx.elicit("Enter the module/extension name to generate tests for:")
        if not response.action == "accept" or not response.data:
            return "Test generation cancelled."
        module_name = response.data
    else:
        await ctx.info(f"Detected generated module: {module_name}")

    aaz_path = Path(f"{paths['cli']}/src/azure-cli/azure/cli/command_modules/{module_name}/aaz")
    if not aaz_path.exists():
        return f"AAZ path not found for module '{module_name}'"

    commands = []
    for file in aaz_path.rglob("*.py"):
        with open(file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip().startswith("def "):
                    commands.append(line.strip().replace("def ", "").split("(")[0])

    test_dir = Path(f"{paths['cli']}/src/azure-cli/azure/cli/command_modules/{module_name}/tests/latest")
    test_dir.mkdir(parents=True, exist_ok=True)
    test_file = test_dir / f"test_{module_name}.py"

    with open(test_file, "w", encoding="utf-8") as f:
        f.write("import unittest\n")
        f.write("from azure.cli.testsdk import ScenarioTest\n\n")
        f.write(f"class {module_name.capitalize()}ScenarioTest(ScenarioTest):\n\n")
        for cmd in commands:
            f.write(f"    def test_{cmd}(self):\n")
            f.write(f"        self.cmd('az {module_name} {cmd} --resource-name test-resource')\n\n")

    await ctx.info(f"Generated test file: {test_file}")
    return f"Test generation completed for module '{module_name}'."