# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
from pathlib import Path
import shutil
import subprocess

import pytest


PWSH = shutil.which("pwsh")
SCRIPT = Path(__file__).resolve().parents[1] / "ParseServiceContactsList.ps1"
pytestmark = pytest.mark.skipif(PWSH is None, reason="PowerShell 7 (pwsh) is required")

# Load only the synchronization function, without fetching the wiki or installing packages.
POWERSHELL_TEST = r"""
$ErrorActionPreference = 'Stop'
$data = [Console]::In.ReadToEnd() | ConvertFrom-Json
$parseErrors = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile(
    $data.script, [ref]$null, [ref]$parseErrors)
if ($parseErrors.Count -gt 0) {
    throw ($parseErrors | Out-String)
}
$function = $ast.Find({
    param($node)
    $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and
        $node.Name -eq 'UpdateServiceContactsTask'
}, $false)
if ($null -eq $function) {
    throw 'UpdateServiceContactsTask was not found'
}
. ([scriptblock]::Create($function.Extent.Text))
$contacts = [System.Collections.Generic.SortedList[System.String, PSCustomObject]]::new()
foreach ($entry in $data.contacts.PSObject.Properties) {
    $contacts.Add($entry.Name, $entry.Value)
}
UpdateServiceContactsTask -ServiceContactsTask $data.task -ServiceContacts $contacts
$data.task | ConvertTo-Json -Depth 64 -Compress
"""


def make_rule(label, mentionees):
    return {
        "if": [
            {"hasLabel": {"label": "Service Attention"}},
            {"hasLabel": {"label": label}},
        ],
        "then": [
            {
                "mentionUsers": {
                    "mentionees": mentionees,
                    "replyTemplate": "cc ${mentionees}",
                    "assignMentionees": "False",
                }
            }
        ],
    }


def make_task(rules):
    return {
        "if": [{"isAction": {"action": "Labeled"}}],
        "then": rules,
        "description": "Triage issues to the service team",
    }


def synchronize(task, contacts):
    result = subprocess.run(
        [PWSH, "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", POWERSHELL_TEST],
        input=json.dumps({
            "script": str(SCRIPT),
            "task": task,
            "contacts": {
                label: make_rule(label, mentionees)
                for label, mentionees in contacts.items()
            },
        }),
        capture_output=True,
        encoding="utf-8",
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return json.loads(result.stdout)


def test_squad_only_difference_does_not_change_the_task():
    task = make_task([
        make_rule("AAD", ["owner", "Azure/act-identity-squad"]),
        make_rule("ACS", ["other-owner", "Azure/act-observability-squad"]),
    ])

    assert synchronize(task, {"AAD": ["owner"], "ACS": ["other-owner"]}) == task


def test_updates_regular_contacts_and_preserves_squads_per_service():
    task = make_task([
        make_rule("AAD", ["old-owner", "Azure/old-team", "Azure/act-identity-squad"]),
        make_rule("ACS", ["old-owner", "Azure/act-observability-squad"]),
    ])

    assert synchronize(task, {"ACS": ["new-acs-owner"], "AAD": ["new-owner", "Azure/new-team"]}) == make_task([
        make_rule("AAD", ["new-owner", "Azure/new-team", "Azure/act-identity-squad"]),
        make_rule("ACS", ["new-acs-owner", "Azure/act-observability-squad"]),
    ])


@pytest.mark.parametrize("mentionee, preserved", [
    ("Azure/act-identity-squad", True),
    ("Azure/act-codegen-extensibility-squad", True),
    ("Azure/act-service2-squad", True),
    ("azure/ACT-Identity-SQUAD", True),
    ("OtherOrg/act-identity-squad", False),
    ("Azure/identity-squad", False),
    ("act-identity-squad", False),
    ("Azure/deployments-owners", False),
    ("Azure/act--squad", False),
    ("Azure/act-identity-squad-extra", False),
    ("Azure/act-identity/other-squad", False),
    ("Azure/act-identity_other-squad", False),
])
def test_only_preserves_matching_squad_teams(mentionee, preserved):
    task = make_task([make_rule("AAD", ["old-owner", mentionee])])
    expected = ["owner", mentionee] if preserved else ["owner"]

    assert synchronize(task, {"AAD": ["owner"]}) == make_task([make_rule("AAD", expected)])


def test_preserves_multiple_squads_without_duplicates():
    task = make_task([make_rule("AAD", [
        "owner", "Azure/act-identity-squad",
        "Azure/act-observability-squad", "Azure/act-identity-squad",
    ])])

    assert synchronize(task, {"AAD": ["owner", "Azure/act-identity-squad"]}) == make_task([
        make_rule("AAD", ["owner", "Azure/act-identity-squad", "Azure/act-observability-squad"]),
    ])


def test_still_adds_and_removes_services_from_the_wiki():
    task = make_task([make_rule("Removed", ["old-owner", "Azure/act-identity-squad"])])

    assert synchronize(task, {"Added": ["new-owner"]}) == make_task([
        make_rule("Added", ["new-owner"]),
    ])


def test_handles_rules_without_label_conditions_or_mention_actions():
    task = make_task([
        {"if": [{"isOpen": True}], "then": [{"addLabel": {"label": "unrelated"}}]},
        make_rule("AAD", ["owner", "Azure/act-identity-squad"]),
    ])

    assert synchronize(task, {"AAD": ["owner"]}) == make_task([
        make_rule("AAD", ["owner", "Azure/act-identity-squad"]),
    ])


def test_can_populate_an_empty_task():
    assert synchronize(make_task([]), {"AAD": ["owner"]}) == make_task([
        make_rule("AAD", ["owner"]),
    ])


def test_empty_contacts_remove_obsolete_rules():
    task = make_task([make_rule("AAD", ["owner", "Azure/act-identity-squad"])])

    assert synchronize(task, {}) == make_task([])


def test_repeated_sync_is_idempotent():
    task = make_task([make_rule("AAD", ["old-owner", "Azure/act-identity-squad"])])
    contacts = {"AAD": ["new-owner"]}
    updated = synchronize(task, contacts)

    assert synchronize(updated, contacts) == updated
