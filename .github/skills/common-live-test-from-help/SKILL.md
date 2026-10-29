---
name: common-live-test-from-help
description: "Use when creating or updating Azure CLI live tests from module help examples. Resolve generated vs manual help precedence, detect missing examples, scaffold scenario tests, and enforce 80% command-level coverage checks."
---

# Common Live Test From Help

Generate consistent live test scaffolding from effective command help.

## Inputs
- Module path, e.g. `src/azure-cli/azure/cli/command_modules/<module-name>`
- Existing help files (`generated/_help.py`, `manual/_help.py`, and top-level `_help.py`)
- Existing tests under `tests/latest/`

## Procedure
1. Resolve final help examples.
- Read top-level `_help.py` for import precedence.
- Read `generated/_help.py` first.
- Read `manual/_help.py` second and treat overlapping entries as overrides.

2. Build command/example inventory.
- Keep only commands with executable `az ...` examples.
- Record commands with missing examples.

3. Ask before manual completion.
- If missing examples exist, ask whether to continue with manual additions.
- Provide the missing command list in the question.

4. Generate or update live test files.
- Update `tests/latest/example_steps.py` with `step_<name>` functions.
- Update `tests/latest/test_<module>_scenario.py` to call all steps.
- Keep or add coverage hooks: `calc_coverage(__file__)` and `raise_if()`.

5. Ask before running tests.
- Prompt user whether to run live tests.
- If yes, run `azdev test <module> --live --no-exitfirst`.

6. Evaluate coverage.
- Parse `tests/latest/*_coverage.md` for command-level coverage.
- If coverage < 80%, warn and recommend adding help examples and corresponding live test steps.

## Output
- Effective help mapping (command -> example source: generated/manual)
- Missing example command list
- Updated test files
- Coverage summary and action items

## Template
- Use [live test template](./references/live-test-template.md) as the base structure.
