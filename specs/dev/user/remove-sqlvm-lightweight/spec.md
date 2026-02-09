# Feature Specification: Remove SQL VM Lightweight Mode

**Feature Branch**: `dev/user/remove-sqlvm-lightweight`  
**Created**: 2026-02-08  
**Status**: Draft  
**Input**: User description: "Remove lightweight mode option from Azure SQL VM extension, defaulting to full mode"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Create SQL VM defaults to Full mode (Priority: P1)

As a customer creating an Azure SQL VM via the CLI, I want the SQL IaaS Extension
to deploy in Full mode by default, so that I have access to all management
features (automated backup, patching, connectivity configuration, SQL assessment)
without needing to specify any additional flags.

**Why this priority**: This is the core behavioral change. Full mode is the
recommended extension mode going forward and should be the default experience
for all new SQL VM registrations.

**Independent Test**: Create a SQL VM with `az sql vm create` without specifying
`--sql-mgmt-type`. Verify the resulting SQL VM resource has
`sqlManagement` set to `Full`.

**Acceptance Scenarios**:

1. **Given** a user runs `az sql vm create` without `--sql-mgmt-type`,
   **When** the SQL VM is created,
   **Then** the `sqlManagement` property on the created resource MUST be `Full`.

2. **Given** a user runs `az sql vm create` with `--sql-mgmt-type Full` (while
   the parameter still exists during deprecation),
   **When** the SQL VM is created,
   **Then** the `sqlManagement` property MUST be `Full` and a deprecation
   warning MUST be emitted.

---

### User Story 2 - Remove LightWeight as an accepted value (Priority: P1)

As a CLI maintainer, I want the `LightWeight` value to no longer be accepted
for `--sql-mgmt-type`, so that customers cannot accidentally deploy the
extension in a limited mode.

**Why this priority**: Removing the LightWeight option is the direct
requirement. Customers relying on lightweight mode need to be moved to full
mode, and allowing LightWeight defeats the purpose of the change.

**Independent Test**: Attempt to run `az sql vm create --sql-mgmt-type LightWeight`.
Verify the command rejects the value or ignores it with a clear warning.

**Acceptance Scenarios**:

1. **Given** a user runs `az sql vm create --sql-mgmt-type LightWeight`,
   **When** the CLI processes the command,
   **Then** the CLI MUST raise a hard error stating that LightWeight mode is
   no longer supported and the user should remove the `--sql-mgmt-type` flag
   (which defaults to Full) or use `NoAgent` if applicable.

2. **Given** a user runs `az sql vm update --sql-mgmt-type LightWeight`,
   **When** the CLI processes the command,
   **Then** the CLI MUST raise a hard error with the same message.

---

### User Story 3 - Restrict --sql-mgmt-type to Full and NoAgent (Priority: P2)

As a CLI maintainer, I want `--sql-mgmt-type` to only accept `Full` and
`NoAgent` values (removing `LightWeight`), so that the parameter remains
available for the NoAgent legacy scenario while preventing LightWeight usage.

**Why this priority**: The parameter must be retained for NoAgent (EOS SQL
2008/R2) but LightWeight must be eliminated. Restricting accepted values
achieves both goals without introducing new flags.

**Independent Test**: Run `az sql vm create --sql-mgmt-type Full` and verify a
deprecation or removal message is displayed. Confirm `az sql vm create --help`
no longer lists `--sql-mgmt-type` (or marks it deprecated).

**Acceptance Scenarios**:

1. **Given** the `--sql-mgmt-type` parameter is removed from `create`,
   **When** a user runs `az sql vm create --sql-mgmt-type Full`,
   **Then** the CLI MUST emit a deprecation warning (or error if fully removed)
   indicating the parameter is no longer needed.

2. **Given** the `--sql-mgmt-type` parameter is removed from `update`,
   **When** a user runs `az sql vm update --sql-mgmt-type Full`,
   **Then** the CLI MUST emit a deprecation warning (or error if fully removed).

---

### User Story 4 - Handle NoAgent mode (Priority: P2)

As a customer with an end-of-support SQL Server 2008/R2 VM, I need to
continue using `--sql-mgmt-type NoAgent` with `--image-sku` and
`--image-offer` to register my VM without an agent.

**Why this priority**: NoAgent is a distinct use case for legacy SQL Server
versions. The existing `--sql-mgmt-type` parameter continues to serve this
purpose without any mechanism change.

**Independent Test**: Run `az sql vm create --sql-mgmt-type NoAgent --image-sku <sku> --image-offer <offer>` and verify successful NoAgent registration.

**Acceptance Scenarios**:

1. **Given** a user needs NoAgent mode for SQL 2008 R2,
   **When** they create a SQL VM with the appropriate flags,
   **Then** the system MUST still allow NoAgent registration with `--image-sku`
   and `--image-offer`.

---

### User Story 5 - Update help text and examples (Priority: P3)

As a CLI user reading documentation, I want the help text and examples for
`az sql vm create` and `az sql vm update` to reflect the new behavior—no
mention of LightWeight mode, and clear guidance that Full mode is the default.

**Why this priority**: Documentation accuracy ensures users understand the
current behavior without confusion.

**Independent Test**: Run `az sql vm create --help` and `az sql vm update --help`.
Verify no references to LightWeight mode remain, and examples reflect
Full mode as default.

**Acceptance Scenarios**:

1. **Given** a user runs `az sql vm create --help`,
   **When** the help text is displayed,
   **Then** it MUST NOT reference LightWeight mode and MUST indicate Full
   mode is the default.

2. **Given** a user runs `az sql vm update --help`,
   **When** the help text is displayed,
   **Then** it MUST NOT reference LightWeight mode.

---

### Edge Cases

- What happens when an existing SQL VM was registered in LightWeight mode and
  a user runs `az sql vm update`? The update should not forcibly change the
  mode, but should no longer offer LightWeight as a settable option.
- What happens when `--sql-mgmt-type NoAgent` is used without the required
  `--image-sku` and `--image-offer`? The existing validation error must
  continue to function.
- What happens when `--least-privilege-mode Enabled` is used? The current
  validator requires `--sql-mgmt-type Full`. Since Full is now the default,
  this validation should still pass but may need updating to no longer
  reference `--sql-mgmt-type` in the error message.
- What happens with existing automation scripts that explicitly pass
  `--sql-mgmt-type LightWeight`? They will receive clear error messages
  indicating the value is no longer supported.

## Clarifications

### Session 2026-02-08

- Q: Should `--sql-mgmt-type` be fully removed or retained for NoAgent? → A: Keep `--sql-mgmt-type` but restrict accepted values to `Full` and `NoAgent` only (remove `LightWeight`).
- Q: Should passing `LightWeight` produce a warning+override or a hard error? → A: Raise a hard error telling the user `LightWeight` is no longer supported.
- Q: How should this change be classified for release? → A: Full breaking change with major release note and migration guidance.
- Q: Should the registration pipeline still be able to create VMs in LightWeight mode? → A: Yes. The server-side registration pipeline retains LightWeight mode; only the Azure CLI blocks it.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The `az sql vm create` command MUST default the `sql_management`
  property to `Full` instead of `LightWeight`.

- **FR-002**: The `LightWeight` value MUST be removed from the set of accepted
  values for `--sql-mgmt-type` on both `create` and `update` commands. Passing
  `LightWeight` MUST raise a hard error (not a warning) with a message
  directing the user to remove the flag or use `NoAgent`.

- **FR-003**: The `--sql-mgmt-type` parameter MUST be retained on both
  `az sql vm create` and `az sql vm update`, but its accepted values MUST
  be restricted to `Full` and `NoAgent` only. The `LightWeight` value MUST
  be rejected with a clear error message.

- **FR-004**: The `--sql-mgmt-type` parameter MUST continue to show a
  deprecation warning when used, since `Full` is now the default and the
  parameter is only needed for the `NoAgent` scenario.

- **FR-005**: The `NoAgent` mode MUST remain accessible via
  `--sql-mgmt-type NoAgent` for end-of-support SQL Server 2008/R2 scenarios.
  No new flags are needed; the existing parameter serves this purpose.

- **FR-006**: The `validate_sqlmanagement` validator MUST be updated to reflect
  the removal of LightWeight mode.

- **FR-007**: The `validate_least_privilege_mode` validator MUST be updated to
  no longer require explicit `--sql-mgmt-type Full`, since Full is now the
  implicit default.

- **FR-008**: All help text MUST be updated to remove references to LightWeight
  mode and reflect the new default behavior.

- **FR-009**: All CLI tests MUST be updated to reflect the new default
  (`Full` instead of `LightWeight`) and to remove test cases that exercise
  LightWeight mode.

- **FR-010**: The changelog MUST be updated with an entry documenting this
  as a full breaking change. The entry MUST include migration guidance
  instructing users to remove `--sql-mgmt-type LightWeight` from scripts
  (Full is now the default) or switch to `--sql-mgmt-type NoAgent` if
  applicable.

### Key Entities

- **SqlVirtualMachine**: The primary resource representing a SQL Server
  instance on an Azure VM. The `sql_management` property controls the
  extension mode (`Full`, `NoAgent`; `LightWeight` being removed).

- **SqlManagementMode enum**: The SDK enum that defines accepted values.
  The CLI must stop exposing `LightWeight` even if the SDK still defines it.

- **IaaS Extension (SQL IaaS Agent)**: The Azure extension installed on the
  VM, whose behavior depends on the management mode.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of new SQL VM creations via `az sql vm create` (without
  explicit mode flag) result in `sqlManagement=Full`.

- **SC-002**: Any CLI invocation with `--sql-mgmt-type LightWeight` produces
  a hard error with an actionable message; the command does not execute.

- **SC-003**: All existing CLI tests pass after the change, with updated
  assertions reflecting the new default.

- **SC-004**: The `az sql vm create --help` and `az sql vm update --help`
  output contains zero references to LightWeight mode.

- **SC-005**: NoAgent mode continues to function correctly for SQL 2008/R2
  scenarios without regression.

- **SC-006**: The `--least-privilege-mode Enabled` flag works without
  requiring an explicit `--sql-mgmt-type Full` argument.

## Assumptions

- The Azure SQL VM SDK server-side API continues to accept `Full` as a valid
  `sql_management` value.
- The server-side registration pipeline continues to support LightWeight mode.
  This CLI change does NOT affect the registration pipeline or the underlying
  API—only the `az sql vm` CLI commands block LightWeight as a user-selectable
  option.
- The `NoAgent` mode remains a valid server-side option and must be preserved.
- The `--sql-mgmt-type` parameter is already marked as deprecated in the
  current codebase; this change completes the deprecation by removing
  LightWeight and making the parameter unnecessary for the common case.
- Existing SQL VMs registered in LightWeight mode (via any pathway) are not
  affected by this CLI change—the server-side resource retains its current
  mode. This change only affects new CLI operations.
