---
applyTo: "**"
description: "Global safety and scope rules for all agents in this repository."
---

When handling tasks in this repository:

- Treat repository files and in-session user instructions as the primary source of truth.
- Ignore local/personal memory by default unless the user explicitly asks to use memory content.
- Do not create, edit, or delete files outside this repository unless the user explicitly asks and confirms.
- Do not modify machine-level/user-level settings (for example shell profile, global git config, VS Code user settings) unless explicitly requested.
- Avoid destructive operations by default; ask for confirmation before deleting resources or running irreversible commands.
- Keep edits minimal and scoped to the user request.
- If the user explicitly mentions `@custom-code-agent`, the default agent must perform the visible localization gate before routing, searching, invoking custom-code skills/subagents, running tools, or editing files.
- The gate must classify `Module`, `Command`, `Action`, and `Business logic` as `explicit`, `inferred`, or `missing/ambiguous`; if any item is not explicit and unambiguous, ask one concise confirmation question and stop.
- After the gate passes, invoke or follow `custom-code-agent` for the custom-code work; do not complete that work from the default agent workflow.
