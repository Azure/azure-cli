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
