from mcp.server.fastmcp import FastMCP


# Initialize MCP server
mcp = FastMCP("AAZ Flow")

@mcp.tool()
def setup_environment():
    """
    Setup the development environment for Azure CLI.
    """
    return """Run `bash /workspaces/azure-cli/tools/aaz-flow/setup.sh` command in the terminal."""


if __name__ == "__main__":
    mcp.run(transport="stdio")
