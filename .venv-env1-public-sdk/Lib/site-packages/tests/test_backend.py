# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import keyring
import keyring.backend
import keyring.backends.chainer
import keyring.errors
import requests

from artifacts_keyring import ArtifactsKeyringBackend, CredentialProvider

import pytest

# Shouldn't be accessed by tests, but needs to be able
# to get past the quick check.
SUPPORTED_HOST = "https://pkgs.dev.azure.com/"


class FakeProvider(object):
    def get_credentials(self, service):
        return "user" + service[-4:], "pass" + service[-4:]


class PasswordsBackend(keyring.backend.KeyringBackend):
    priority = 9.9

    def __init__(self):
        self.passwords = {}

    def get_password(self, system, username):
        return self.passwords.get((system, username))

    def set_password(self, system, username, password):
        self.passwords[system, username] = password

    def delete_password(self, system, username):
        try:
            del self.passwords[system, username]
        except LookupError:
            raise keyring.errors.PasswordDeleteError(username)


class MockGetResponse:
    status_code = 200


@pytest.fixture
def only_backend():
    previous = keyring.get_keyring()
    backend = ArtifactsKeyringBackend()
    keyring.set_keyring(backend)
    yield backend
    keyring.set_keyring(previous)


@pytest.fixture
def passwords(monkeypatch):
    passwords_backend = PasswordsBackend()

    def mock_get_all_keyring():
        return [ArtifactsKeyringBackend(), passwords_backend]

    monkeypatch.setattr(keyring.backend, "get_all_keyring", mock_get_all_keyring)

    chainer_backend = keyring.backends.chainer.ChainerBackend()

    previous = keyring.get_keyring()
    keyring.set_keyring(chainer_backend)
    yield passwords_backend.passwords
    keyring.set_keyring(previous)


@pytest.fixture
def fake_provider(monkeypatch):
    monkeypatch.setattr(ArtifactsKeyringBackend, "_PROVIDER", FakeProvider)


@pytest.fixture
def validating_provider(monkeypatch):
    def mock_get_credentials(self, url, is_retry):
        return url, is_retry

    def mock_requests_get(url, auth):
        response = MockGetResponse()
        response.status_code = int(url[:3])
        return response

    monkeypatch.setattr(CredentialProvider, "_get_credentials_from_credential_provider", mock_get_credentials)
    monkeypatch.setattr(requests, "get", mock_requests_get)

    yield CredentialProvider()


def test_get_credential_unsupported_host(only_backend):
    assert keyring.get_credential("https://example.com", None) == None


def test_get_credential(only_backend, fake_provider):
    creds = keyring.get_credential(SUPPORTED_HOST + "1234", None)
    assert creds.username == "user1234"
    assert creds.password == "pass1234"


def test_set_password_raises(only_backend):
    with pytest.raises(NotImplementedError):
        keyring.set_password("SYSTEM", "USERNAME", "PASSWORD")


def test_set_password_fallback(passwords, fake_provider):
    # Ensure we are getting good credentials
    assert keyring.get_credential(SUPPORTED_HOST + "1234", None).password == "pass1234"

    assert keyring.get_password("SYSTEM", "USERNAME") is None
    keyring.set_password("SYSTEM", "USERNAME", "PASSWORD")
    assert passwords["SYSTEM", "USERNAME"] == "PASSWORD"
    assert keyring.get_password("SYSTEM", "USERNAME") == "PASSWORD"
    assert keyring.get_credential("SYSTEM", "USERNAME").username == "USERNAME"
    assert keyring.get_credential("SYSTEM", "USERNAME").password == "PASSWORD"

    # Ensure we are getting good credentials
    assert keyring.get_credential(SUPPORTED_HOST + "1234", None).password == "pass1234"


def test_delete_password_raises(only_backend):
    with pytest.raises(NotImplementedError):
        keyring.delete_password("SYSTEM", "USERNAME")


def test_delete_password_fallback(passwords, fake_provider):
    # Ensure we are getting good credentials
    assert keyring.get_credential(SUPPORTED_HOST + "1234", None).password == "pass1234"

    passwords["SYSTEM", "USERNAME"] = "PASSWORD"
    keyring.delete_password("SYSTEM", "USERNAME")
    assert keyring.get_password("SYSTEM", "USERNAME") is None
    assert not passwords
    with pytest.raises(keyring.errors.PasswordDeleteError):
        keyring.delete_password("SYSTEM", "USERNAME")


def test_cannot_delete_password(passwords, fake_provider):
    # Ensure we are getting good credentials
    creds = keyring.get_credential(SUPPORTED_HOST + "1234", None)
    assert creds.username == "user1234"
    assert creds.password == "pass1234"

    with pytest.raises(keyring.errors.PasswordDeleteError):
        keyring.delete_password(SUPPORTED_HOST + "1234", creds.username)


def test_retry_on_invalid_credentials(validating_provider):
     # No credentials returned when it can already authenticate without them
    username, password = validating_provider.get_credentials("200" + SUPPORTED_HOST)
    assert username == None and password == None

    # Credentials returned from first call with IsRetry=false
    username, password = validating_provider.get_credentials("200" + SUPPORTED_HOST + "pypi/upload")
    assert password == False

    # Credentials returned from second call with IsRetry=true
    username, password = validating_provider.get_credentials("401" + SUPPORTED_HOST)
    assert password == True

    username, password = validating_provider.get_credentials("403" + SUPPORTED_HOST)
    assert password == True

    username, password = validating_provider.get_credentials("500" + SUPPORTED_HOST)
    assert password == True
