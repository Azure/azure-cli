import os
from pathlib import Path
from fastmcp import FastMCP, Context
from models import AAZRequest
from helpers import generate_tests, execute_commands, validate_paths, get_extension_name, get_swagger_config

mcp = FastMCP("AAZ Flow")

@mcp.tool(
    name="az_cli_generate_help",
    description="Explains how to correctly call the az_cli_generate tool."
)
async def generate_help(ctx: Context):
    help_message = {
        "tool": "az_cli_generate",
        "description": "Generate Azure CLI commands from Swagger specs.",
        "parameters": {},
        "usage": "Call with no parameters, e.g. {}"
    }
    await ctx.info("az_cli_generate_help retrieved.")
    return help_message

@mcp.tool(
    name="az_cli_generate",
    description="Generate Azure CLI commands from Swagger specs."
)
async def generate_code(ctx: Context):
    await ctx.info("Initiating Azure CLI code generation workflow.")

    await ctx.report_progress(5, 100)

    paths = await validate_paths(ctx)
    if not paths:
        return "Code generation cancelled."
    await ctx.report_progress(20, 100)

    extension_name = await get_extension_name(ctx)
    if not extension_name:
        return "Code generation cancelled."
    await ctx.report_progress(40, 100)

    swagger_config = await get_swagger_config(ctx, paths, service_name=extension_name)

    if not swagger_config:
        return "Code generation cancelled."
    await ctx.report_progress(60, 100)

    request = AAZRequest(
        extension_or_module_name=extension_name,
        swagger_module_path=swagger_config["file"],
        resource_provider=swagger_config["resource_provider"],
        swagger_tag=swagger_config["swagger_tag"]
    )

    await execute_commands(ctx, paths, request)
    await ctx.report_progress(100, 100)
    await ctx.info(f"Code generation completed for extension/module '{extension_name}'.")

    ctx.generated_module = extension_name

    await ctx.info("Automatically generating tests for the newly generated module...")
    try:
        test_result = await generate_tests(ctx)
        await ctx.info(f"Automatic test generation result: {test_result}")
    except Exception as e:
        await ctx.info(f"Automatic test generation failed: {str(e)}")

    return f"Code generation and test generation completed for extension/module '{extension_name}'."

if __name__ == "__main__":
    mcp.run(transport="stdio")