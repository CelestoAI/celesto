# Copyright 2026 Celesto AI
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""`celesto auth login/status/logout`."""

import json
import os
from unittest.mock import Mock

import pytest
from click.testing import CliRunner

from celesto.cli import _credentials
from celesto.cli.commands.app import build_cli
from celesto.cli.main import main


@pytest.fixture(autouse=True)
def isolated_credentials(monkeypatch, tmp_path):
    monkeypatch.setattr("celesto.cli.commands.app._before_command", lambda **kwargs: None)
    monkeypatch.setattr(_credentials, "CREDENTIALS_PATH", tmp_path / "credentials")


def test_login_stores_credentials_on_success(monkeypatch, capsys):
    fetch = Mock(return_value="anurag@senseloaf.com")
    monkeypatch.setattr("celesto.cli.main._fetch_authenticated_email", fetch)

    assert main(["auth", "login", "--api-key", "celesto_sk_test", "--json"]) == 0

    fetch.assert_called_once_with("https://api.celesto.ai", "celesto_sk_test")
    payload = json.loads(capsys.readouterr().out)
    assert payload["data"] == {
        "email": "anurag@senseloaf.com",
        "base_url": "https://api.celesto.ai",
    }
    assert _credentials.read_credentials() == {
        "api_key": "celesto_sk_test",
        "email": "anurag@senseloaf.com",
        "base_url": "https://api.celesto.ai",
    }


def test_login_rejects_invalid_key_without_storing(monkeypatch, capsys):
    monkeypatch.setattr(
        "celesto.cli.main._fetch_authenticated_email",
        Mock(side_effect=ValueError("That API key was not accepted by the server.")),
    )

    assert main(["auth", "login", "--api-key", "bad", "--json"]) == 1

    payload = json.loads(capsys.readouterr().out)
    assert payload["error"]["message"] == "That API key was not accepted by the server."
    assert _credentials.read_credentials() is None


def test_login_rejects_remote_plaintext_http(capsys):
    assert (
        main(
            [
                "auth",
                "login",
                "--api-key",
                "celesto_sk_test",
                "--base-url",
                "http://example.com",
                "--json",
            ]
        )
        == 1
    )
    payload = json.loads(capsys.readouterr().out)
    assert "HTTPS" in payload["error"]["message"]


def test_login_allows_localhost_http(monkeypatch):
    monkeypatch.setattr(
        "celesto.cli.main._fetch_authenticated_email", lambda base_url, api_key: "a@b.com"
    )
    assert (
        main(
            [
                "auth",
                "login",
                "--api-key",
                "celesto_sk_test",
                "--base-url",
                "http://localhost:8000",
            ]
        )
        == 0
    )


def test_login_json_without_api_key_fails_instead_of_prompting(capsys):
    assert main(["auth", "login", "--json"]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert "prompt" in payload["error"]["message"]


def test_login_prompts_when_api_key_omitted(monkeypatch):
    monkeypatch.setattr(
        "celesto.cli.main._fetch_authenticated_email", Mock(return_value="anurag@senseloaf.com")
    )
    result = CliRunner().invoke(build_cli(), ["auth", "login"], input="celesto_sk_prompted\n")
    assert result.exit_code == 0
    assert "Logged in as anurag@senseloaf.com" in result.output
    assert _credentials.read_api_key() == "celesto_sk_prompted"


def test_status_reports_not_logged_in(capsys):
    assert main(["auth", "status", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["data"] == {
        "authenticated": False,
        "message": "Not logged in. Run 'celesto auth login'.",
    }


def test_status_revalidates_stored_key(monkeypatch, capsys):
    _credentials.write_credentials(
        api_key="celesto_sk_test", email="stale@example.com", base_url="https://api.celesto.ai"
    )
    fetch = Mock(return_value="anurag@senseloaf.com")
    monkeypatch.setattr("celesto.cli.main._fetch_authenticated_email", fetch)

    assert main(["auth", "status", "--json"]) == 0

    fetch.assert_called_once_with("https://api.celesto.ai", "celesto_sk_test")
    payload = json.loads(capsys.readouterr().out)
    assert payload["data"] == {
        "authenticated": True,
        "email": "anurag@senseloaf.com",
        "base_url": "https://api.celesto.ai",
    }


def test_status_surfaces_revoked_key(monkeypatch, capsys):
    _credentials.write_credentials(
        api_key="celesto_sk_test", email="anurag@senseloaf.com", base_url="https://api.celesto.ai"
    )
    monkeypatch.setattr(
        "celesto.cli.main._fetch_authenticated_email",
        Mock(side_effect=ValueError("That API key was not accepted by the server.")),
    )

    assert main(["auth", "status", "--json"]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["error"]["message"] == "That API key was not accepted by the server."


def test_logout_removes_stored_credentials(capsys):
    _credentials.write_credentials(api_key="k", email="e", base_url="https://api.celesto.ai")

    assert main(["auth", "logout", "--json"]) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["data"] == {"removed": True, "message": "Logged out."}
    assert _credentials.read_credentials() is None


def test_logout_is_idempotent(capsys):
    assert main(["auth", "logout", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["data"] == {"removed": False, "message": "Already logged out."}


def test_credentials_file_written_with_owner_only_permissions():
    _credentials.write_credentials(api_key="k", email="e", base_url="https://api.celesto.ai")
    mode = _credentials.CREDENTIALS_PATH.stat().st_mode & 0o777
    assert mode == 0o600


def test_write_credentials_tightens_permissions_on_existing_file():
    _credentials.CREDENTIALS_PATH.parent.mkdir(parents=True, exist_ok=True)
    _credentials.CREDENTIALS_PATH.write_text("{}")
    _credentials.CREDENTIALS_PATH.chmod(0o644)

    _credentials.write_credentials(api_key="k", email="e", base_url="https://api.celesto.ai")

    mode = _credentials.CREDENTIALS_PATH.stat().st_mode & 0o777
    assert mode == 0o600


def test_write_credentials_keeps_existing_file_if_replace_fails(monkeypatch):
    _credentials.write_credentials(
        api_key="old", email="old@example.com", base_url="https://api.celesto.ai"
    )
    original = _credentials.CREDENTIALS_PATH.read_text()
    original_mode = _credentials.CREDENTIALS_PATH.stat().st_mode & 0o777

    def fail_replace(source, destination):
        assert source != destination
        assert source.stat().st_mode & 0o777 == 0o600
        raise OSError("replace failed")

    monkeypatch.setattr(os, "replace", fail_replace)
    with pytest.raises(OSError, match="replace failed"):
        _credentials.write_credentials(
            api_key="new", email="new@example.com", base_url="https://api.celesto.ai"
        )

    assert _credentials.CREDENTIALS_PATH.read_text() == original
    assert _credentials.CREDENTIALS_PATH.stat().st_mode & 0o777 == original_mode
    assert list(_credentials.CREDENTIALS_PATH.parent.iterdir()) == [_credentials.CREDENTIALS_PATH]
