---
applyTo: "{src/azure-cli/HISTORY.rst,src/azure-cli-core/HISTORY.rst}"
description: "Do not manually edit HISTORY.rst files; release history is generated automatically."
---

When reviewing or editing changes in this repository:

- Do **not** manually add, modify, or delete entries in any `HISTORY.rst` file
  (for example `src/azure-cli/HISTORY.rst` or `src/azure-cli-core/HISTORY.rst`).
  Release history notes are generated automatically from PR titles and descriptions
  by the release pipeline (`scripts/release/generate_history_notes.py`).
- During PR review, if a pull request contains manual changes to a `HISTORY.rst`
  file, request that the author revert those changes while preserving the
  functional (non-`HISTORY.rst`) changes. Reviewers consistently ask contributors
  to "revert the changes to the HISTORY.rst, as the history notes would be
  generated automatically."
- To control what appears in the release history, use the PR title and the
  `History Notes` section of the PR description instead of editing `HISTORY.rst`:
  - A `[Component Name]` title prefix marks a customer-facing change that will be
    added to `HISTORY.rst`; a `{Component Name}` prefix marks a change that will
    **not** be included.
  - See `doc/authoring_command_modules/README.md` ("Format PR Title" and
    "Format PR Description") for the required format.
- The only exception is a **Hotfix** PR targeting the `release` branch: per
  `doc/authoring_command_modules/README.md`, customer-facing hotfixes must
  manually add their history notes because the auto-generated notes ignore
  PRs marked `Hotfix`. Outside this hotfix flow, manual `HISTORY.rst` edits
  should be reverted.
