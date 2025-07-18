FROM mcr.microsoft.com/devcontainers/python:3.12

# Copy uv binaries for virtual environment management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install git and mcp, create /workspaces-src with correct ownership
RUN apt-get update && apt-get install -y git \
    && pip install --no-cache-dir mcp \
    && mkdir -p /workspaces-src \
    && chown -R vscode:vscode /workspaces-src

# Ensure bash is default shell
SHELL ["/bin/bash", "-c"]