# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from fastmcp import FastMCP, Context
from helpers import get_name, run_code_generation, get_module_name, get_validated_paths
from testgen import generate_tests

mcp = FastMCP("AAZ Flow")

async def run_test_generation(ctx: Context, paths: dict):
    await ctx.info("Automatically generating tests for the newly generated module...")
    try:
        test_result = await generate_tests(ctx, paths)
        await ctx.info(f"Automatic test generation result: {test_result}")
    except Exception as e:
        await ctx.info(f"Automatic test generation failed: {str(e)}")

async def run_full_generation(ctx: Context, name: str, paths: dict):
    await ctx.report_progress(40, 100)
    name, error = await run_code_generation(ctx, name, paths)
    if error:
        return error
    await ctx.report_progress(60, 100)
    await ctx.report_progress(100, 100)
    await run_test_generation(ctx, paths)
    return f"Code generation and test generation completed for extension/module '{name}'."

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

    paths = await get_validated_paths(ctx)
    if not paths:
        return "Test generation cancelled."

    module_name = await get_module_name(ctx, module_name)
    if not module_name:
        return "Test generation cancelled."

    await run_test_generation(ctx, paths)

    return f"Test generation completed for extension/module '{module_name}'."

@mcp.tool(
    name="az_cli_generate_code_direct_help",
    description="Explains how to correctly call the az_cli_generate tool directly if the user has a specific module/extension in mind.",
)
async def generate_code_direct_help(ctx: Context):
    help_message = {
        "tool": "az_cli_generate_code_direct",
        "description": "Generate Azure CLI commands from Swagger specs when the user has a specific module/extension in mind.",
        "parameters": {
            "module_name": "Name of the module/extension to generate code for"
        },
        "usage": "Call with module name parameter, e.g. {'module_name': 'my-extension'}",
    }
    await ctx.info("az_cli_generate_code_direct_help retrieved.")
    return help_message

@mcp.tool(
    name="az_cli_generate_code_direct",
    description="Generate Azure CLI commands from Swagger specs when the user has a specific module/extension in mind.",
)
async def generate_code_direct(ctx: Context, module_name: str):
    await ctx.info("Initiating Azure CLI code generation workflow with specified module/extension.")
    await ctx.report_progress(5, 100)

    paths = await get_validated_paths(ctx)
    if not paths:
        return "Code generation cancelled."
    await ctx.report_progress(20, 100)

    if not module_name:
        return "Code generation cancelled."

    return await run_full_generation(ctx, module_name, paths)

@mcp.tool(
    name="az_cli_generate",
    description="Generate Azure CLI commands from Swagger specs.",
)
async def generate_code(ctx: Context):
    await ctx.info("Initiating Azure CLI code generation workflow.")
    await ctx.report_progress(5, 100)

    paths = await get_validated_paths(ctx)
    if not paths:
        return "Code generation cancelled."
    await ctx.report_progress(20, 100)

    name = await get_name(ctx)
    if not name:
        return "Code generation cancelled."

    return await run_full_generation(ctx, name, paths)

if __name__ == "__main__":
    mcp.run(transport="stdio")
