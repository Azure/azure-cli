# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from fastmcp import FastMCP, Context
from models import AAZRequest
from helpers import execute_commands, validate_paths, get_name, get_swagger_config
from testgen import generate_tests

mcp = FastMCP("AAZ Flow")


@mcp.tool(
    name="az_cli_generate_help",
    description="Explains how to correctly call the az_cli_generate tool.",
)
async def generate_help(ctx: Context):
    help_message = {
        "tool": "az_cli_generate",
        "description": "Generate Azure CLI commands from Swagger specs.",
        "parameters": {},
        "usage": "Call with no parameters, e.g. {}",
    }
    await ctx.info("az_cli_generate_help retrieved.")
    return help_message

@mcp.tool(
    name="az_cli_generate_tests_help",
    description="Explains how to correctly call the az_cli_generate_tests tool.",
)
async def generate_tests_help(ctx: Context):
    help_message = {
        "tool": "az_cli_generate_tests",
        "description": (
            "Generate tests for the newly generated Azure CLI commands. "
            "Should only be called independently if the user has already "
            "generated a module/extension or explicitly wants to only generate tests."
        ),
        "parameters": {
            "module_name": "Name of the module/extension to generate tests for"
        },
        "usage": "Call with module name parameter, e.g. {'module_name': 'my-extension'}",
    }
    await ctx.info("az_cli_generate_tests_help retrieved.")
    return help_message

@mcp.tool(
    name="az_cli_generate_tests",
    description="Generate tests for the newly generated Azure CLI commands.",
)
async def generate_tests_tool(ctx: Context, module_name: str | None = None):
    await ctx.info("Initiating Azure CLI test generation workflow.")

    paths = await validate_paths(ctx)
    if not paths:
        return "Test generation cancelled."

    module_name = setattr(ctx, "generated_module", module_name)
    if not module_name:
        response = await ctx.elicit(
            "Enter the module/extension name to generate tests for:"
        )
        if response.action != "accept" or not response.data:
            return "Test generation cancelled."
        module_name = response.data
    else:
        await ctx.info(f"Detected generated module: {module_name}")

    ctx.generated_module = module_name

    await ctx.info(f"Automatically generating tests for the module {module_name}...")
    try:
        test_result = await generate_tests(ctx, paths)
        await ctx.info(f"Automatic test generation result: {test_result}")
    except Exception as e:
        await ctx.info(f"Automatic test generation failed: {str(e)}")

    return f"Test generation completed for extension/module '{module_name}'."

@mcp.tool(
    name="az_cli_generate",
    description="Generate Azure CLI commands from Swagger specs.",
)
async def generate_code(ctx: Context):
    await ctx.info("Initiating Azure CLI code generation workflow.")

    await ctx.report_progress(5, 100)

    paths = await validate_paths(ctx)
    if not paths:
        return "Code generation cancelled."
    await ctx.report_progress(20, 100)

    name = await get_name(ctx)
    if not name:
        return "Code generation cancelled."
    await ctx.report_progress(40, 100)

    swagger_config = await get_swagger_config(ctx, paths, service_name=name)

    if not swagger_config:
        return "Code generation cancelled."
    await ctx.report_progress(60, 100)

    request = AAZRequest(
        name=name,
        swagger_module_path=swagger_config["file"],
        resource_provider=swagger_config["resource_provider"],
        swagger_tag=swagger_config["swagger_tag"],
    )

    await execute_commands(ctx, paths, request)
    await ctx.report_progress(100, 100)
    await ctx.info(f"Code generation completed for extension/module '{name}'.")

    ctx.generated_module = name

    await ctx.info("Automatically generating tests for the newly generated module...")
    try:
        test_result = await generate_tests(ctx, paths)
        await ctx.info(f"Automatic test generation result: {test_result}")
    except Exception as e:
        await ctx.info(f"Automatic test generation failed: {str(e)}")

    return (
        f"Code generation and test generation completed for extension/module '{name}'."
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")
