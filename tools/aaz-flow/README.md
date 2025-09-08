## AAZ MCP Server
MCP Server for the AAZ API, enabling prune command-line interface, implement custom logic, generate meaningful example, and more.

Please note that AAZ Flow is currently in early development. The functionality and available tools are subject to change and expansion as we continue to develop and improve the server.

### Tools
`generate_code`

## Implementation
1. Performs elicitation for user input to perform workflow
2. Generates content using llm sampling
3. Executes AAZ Flow commands directly
4. Generates tests using llm sampling
5. Uses tool transformation to make the internal tooling more friendly for llms