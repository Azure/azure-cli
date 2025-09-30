# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Prompt templates and static guidance for AAZ Flow tools."""


def get_testgen_static_instructions() -> str:
    return (
        "You are generating Azure CLI scenario tests for a new module.\n"
        "Follow the style used by azure-cli scenario tests. Keep tests idempotent and light.\n"
        "Generate tests that achieve at least 80%% coverage of methods and parameters covering primary commands for the target module.\n"
        "To understand the primary commands that need to be tested, read through and understand the target module's generated AAZ commands.\n"
        "Constraints: \n"
        "- Include necessary imports: azure.cli.testsdk imports and others only as required and seen in reference.\n"
        "- Use self.kwargs for dynamic values.\n"
        "- Use ResourceGroupPreparer if a resource group is implied.\n"
        "- Add minimal checks (e.g., self.check) where sensible.\n"
        "- Keep tests safe-by-default; avoid destructive operations unless clearly required.\n"
        "- Ensure tests can run in parallel without conflicts.\n"
        "- If tests are large and can be safely and logically split, create multiple test methods (i.e. avoid a single CRUD test if possible, split it into multiple tests if logically and safely separable).\n"
        "- Output only valid Python code for the test file, nothing else."
    )


REF_STYLE_LABEL = "Read and reference the following test files (do not copy verbatim, just follow structure):\n"
