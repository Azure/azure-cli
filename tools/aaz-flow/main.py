from mcp.server.fastmcp import FastMCP


# Initialize MCP server
mcp = FastMCP("AAZ Flow")

@mcp.tool()
def setup_environment():
    """
    Setup the development environment for Azure CLI.
    """
    pass


if __name__ == "__main__":
    mcp.run(transport="stdio")
