---
applyTo: "src/azure-cli/azure/cli/command_modules/**/{custom.py,commands.py,_params.py,_help.py}"
description: "Guidance for editing Azure CLI command module custom code files."
---

When editing Azure CLI command modules:

- Keep command registration, parameters, and handlers in sync.
- If a new command is added, wire it in commands.py and define args in _params.py.
- Keep return shapes compatible with existing CLI output patterns.
- Keep help/examples aligned with command behavior.
- Prefer concise error messages through CLIError when user input is invalid.
- Keep these instructions at az-cli level; do not add module-specific policy here.
- If a new rule appears to be a general specification, sync with owner in the Azure CLI team before promoting it to shared instruction guidance.

Before generating or modifying custom code, read and apply these repository docs:

- doc/authoring_command_modules/authoring_commands.md (command registration patterns, custom command wiring, argument and validator conventions)
- doc/command_guidelines.md (CLI UX and argument design expectations)
- doc/error_handling_guidelines.md (preferred Azure CLI error types and patterns)
- doc/authoring_help.md (help authoring format in _help.py/help.yaml)
- doc/reference_doc_guidelines.md (example quality and formatting requirements)
- doc/authoring_tests.md (test coverage and scenario test expectations)
