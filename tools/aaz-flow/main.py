# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import os
from mcp.server.fastmcp import FastMCP

# Initialize MCP server
mcp = FastMCP("AAZ Flow")


@mcp.tool()
def generate_code(
        extension_or_module_name: str,
        swagger_module_path: str,
        resource_provider: str,
        swagger_tag: str,
):
    # Generate Azure CLI commands based on Swagger specifications
    aaz_path = os.getenv("AAZ_PATH", "/workspaces/aaz")
    cli_path = os.getenv("CLI_PATH", "/workspaces/azure-cli")
    cli_extension_path = os.getenv("CLI_EXTENSION_PATH", "/workspaces/azure-cli-extensions")
    swagger_path = os.getenv("SWAGGER_PATH", "/workspaces/azure-rest-api-specs")

    swagger_module = os.path.split(swagger_module_path)[-1]

    des = (
        f"Just run the following command in the terminal: 'aaz-dev command-model generate-from-swagger --swagger-path {swagger_path} --swagger-module-path {swagger_module_path} --aaz-path {aaz_path} --module {swagger_module} --resource-provider {resource_provider} --swagger-tag {swagger_tag}'",
        f"After the command is run successfully, then run the following command: 'aaz-dev cli generate-by-swagger-tag --aaz-path {aaz_path} --cli-path {cli_path} --cli-extension-path {cli_extension_path} --extension-or-module-name {extension_or_module_name} --swagger-module-path {swagger_module_path} --resource-provider {resource_provider} --swagger-tag {swagger_tag} --profile latest'",
        f"After the command is run successfully, this task will be marked as completed.",
    )
    return des


if __name__ == "__main__":
    mcp.run(transport="stdio")
