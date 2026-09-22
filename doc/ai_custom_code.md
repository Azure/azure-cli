# AI-Assisted Custom Code Authoring

This guide explains how Azure CLI contributors can use Copilot custom agents and OpenSpec to add or update command module custom code.

## Summary

Use `@custom-code-agent` for small, clear implementation tasks that do not need a durable spec record. Use OpenSpec for larger or user-facing behavior changes where proposal, design, tasks, and final specs should be reviewed and preserved.

## Available Custom Code Agent

- [custom-code.agent.md](../.github/agents/custom-code.agent.md): Focused on Azure CLI command module custom code changes, including AAZ subclass custom, legacy SDK-backed custom, and legacy non-SDK custom.

<!-- Hidden for now.
- live-test.agent.md: Generates or updates live tests from effective help content.
- pr-generation.agent.md: Generates PR title and description with the `[AI][<module-name>]` title prefix.
-->

## How To Use Agents

Call an agent explicitly from Copilot Chat when the change is small, local, and does not need an OpenSpec record:

```text
@custom-code-agent

Module: <module-name>
Command: az <module> <command-group> <command-or-action>
Action: <add validation | update behavior | add parameter | fix bug | other>
Business logic: <what should change, including important conditions and expected errors/output>
```

Required inputs are the module name, related command, intended action, and business logic. Add file paths, API versions, SDK readiness, examples, or links when they are relevant.

Use `custom-code-agent` for implementation-focused changes where the requirement is already clear and the expected edit area is limited to Azure CLI command module custom code.

## OpenSpec Workflow

Use OpenSpec when a change should have a durable proposal, design, task list, and spec delta before implementation. This is the preferred path for larger changes, public command behavior changes, parameter or validation changes, and work that needs reviewable design context.

Common entry points:

- Propose a change with [/opsx:propose](../.github/prompts/opsx-propose.prompt.md).
- Implement a proposed change with [/opsx:apply](../.github/prompts/opsx-apply.prompt.md).
- Revise an existing change with [/opsx:update](../.github/prompts/opsx-update.prompt.md).
- Archive a completed change with [/opsx:archive](../.github/prompts/opsx-archive.prompt.md).

Local OpenSpec configuration and examples:

- [openspec/config.yaml](../openspec/config.yaml)

The `openspec/changes/` folder is a local development workspace for in-progress proposals, designs, tasks, and archived change artifacts. Keep the folder in the repository, but ignore its contents in git. The repository should keep final specs under `openspec/specs/`.

The `openspec/specs/` folder is reserved for final specs that should be committed after a change is accepted or archived. Keep the folder in the repository with `.gitkeep` until there are real specs to track.

## OpenSpec And Agents

OpenSpec and agents are complementary:

- OpenSpec records what should change, why it should change, the selected design, tasks, and acceptance criteria.
- Agents execute focused implementation work, such as editing custom command code.
- Small, obvious edits can go directly to `@custom-code-agent` without creating a spec.
- Larger or user-facing behavior changes should start with `/opsx:propose`, then use `/opsx:apply` to implement the recorded plan.
- If an OpenSpec design already records the custom-code route, agents should follow that route instead of re-deciding it during implementation.

## When To Use Agents vs Skills vs Instructions

- Agents: Isolated, focused workflow or specialized mode
- Skills: Reusable task playbooks loaded on demand
- Instructions: Always-on or file-scoped coding rules

## Governance

- Common skills are owned by the Azure CLI team.
- If the common skills are not sufficient, service teams and developers are welcome to add module-level skills for their own workflows.
- Module skill names must follow: `module-<module-name>`.
- The Azure CLI team may selectively generalize module-level skills into common skills when they prove useful across modules.
- We expect sub-agents to provide generalized capabilities instead of module-specific behavior.
- Agent instructions are expected to be at az-cli level, not module-local policy.
- If a specification is general and reusable across modules, align with owner before promoting it to shared instruction guidance.
