#!/usr/bin/env python3
"""
Helper for non-interactive Azure CLI login in CI and automation.
This script prints the recommended `az login` command for the detected environment.
It does not execute commands by default to keep unit testing simple and safe.
"""
import os
import sys
import argparse


def detect_mode(env=os.environ):
    if env.get("AZURE_CLIENT_ID") and env.get("AZURE_CLIENT_SECRET") and env.get("AZURE_TENANT_ID"):
        return "service-principal"
    if env.get("AZURE_FEDERATED_TOKEN_FILE"):
        return "workload-identity"
    if env.get("AZURE_CLIENT_ID") and env.get("AZURE_FEDERATED_TOKEN_FILE"):
        return "workload-identity"
    if env.get("AZURE_USE_MANAGED_IDENTITY") == "true" or env.get("MSI_ENDPOINT"):
        return "managed-identity"
    return "unknown"


def build_command(mode, env=os.environ):
    if mode == "service-principal":
        return (
            f"az login --service-principal -u \"{env.get('AZURE_CLIENT_ID')}\" -p \"{env.get('AZURE_CLIENT_SECRET')}\" --tenant \"{env.get('AZURE_TENANT_ID')}\""
        )
    if mode == "workload-identity":
        # Assumes federated token file path in AZURE_FEDERATED_TOKEN_FILE
        token_file = env.get("AZURE_FEDERATED_TOKEN_FILE")
        if token_file:
            return f"az login --federated-token @\"{token_file}\" --allow-no-subscriptions"
        return "# workload-identity detected but AZURE_FEDERATED_TOKEN_FILE not set"
    if mode == "managed-identity":
        return "az login --identity"
    return "# Unable to detect non-interactive auth mode. Use 'az login --help'"


def main():
    parser = argparse.ArgumentParser(description="Detect environment and print recommended az login command.")
    parser.add_argument("--run", action="store_true", help="Execute the suggested az login command")
    args = parser.parse_args()

    mode = detect_mode()
    cmd = build_command(mode)
    print(f"Detected mode: {mode}")
    print(cmd)

    if args.run:
        print("Execution requested. Running the command...")
        rc = os.system(cmd)
        sys.exit(rc)


if __name__ == "__main__":
    main()
