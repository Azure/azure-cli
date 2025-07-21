FROM mcr.microsoft.com/devcontainers/python:3.12

# Copy binaries from the official
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Remove after production
RUN pip install --no-cache-dir mcp
