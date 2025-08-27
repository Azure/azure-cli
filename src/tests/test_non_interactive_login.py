import os
import tempfile
import pytest
from scripts import non_interactive_login as nil


def test_detect_service_principal(monkeypatch):
    monkeypatch.setenv("AZURE_CLIENT_ID", "cid")
    monkeypatch.setenv("AZURE_CLIENT_SECRET", "secret")
    monkeypatch.setenv("AZURE_TENANT_ID", "tid")
    assert nil.detect_mode() == "service-principal"


def test_detect_workload_identity(monkeypatch, tmp_path):
    token_file = tmp_path / "token.txt"
    token_file.write_text("token")
    monkeypatch.setenv("AZURE_FEDERATED_TOKEN_FILE", str(token_file))
    assert nil.detect_mode() == "workload-identity"


def test_detect_managed_identity(monkeypatch):
    monkeypatch.setenv("AZURE_USE_MANAGED_IDENTITY", "true")
    assert nil.detect_mode() == "managed-identity"


def test_build_command_service_principal(monkeypatch):
    monkeypatch.setenv("AZURE_CLIENT_ID", "cid")
    monkeypatch.setenv("AZURE_CLIENT_SECRET", "secret")
    monkeypatch.setenv("AZURE_TENANT_ID", "tid")
    cmd = nil.build_command("service-principal")
    assert "az login --service-principal" in cmd
    assert "cid" in cmd


def test_build_command_workload_identity(monkeypatch, tmp_path):
    token_file = tmp_path / "token.txt"
    token_file.write_text("token")
    monkeypatch.setenv("AZURE_FEDERATED_TOKEN_FILE", str(token_file))
    cmd = nil.build_command("workload-identity")
    assert "--federated-token" in cmd


def test_build_command_managed_identity():
    cmd = nil.build_command("managed-identity")
    assert cmd == "az login --identity"
