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

"""Local storage for the Celesto Cloud API key set by ``celesto auth login``.

Mirrors the SDKs' own auth model (`CELESTO_API_KEY` env var or an explicit
`api_key=`): this file is just a third, lower-priority place to find that same
key so `--cloud` commands work after `celesto auth login` without exporting
anything.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import TypedDict

CREDENTIALS_PATH = Path.home() / ".celesto" / "credentials"


class StoredCredentials(TypedDict):
    api_key: str
    email: str
    base_url: str


def read_credentials() -> StoredCredentials | None:
    """Return the stored credentials, or None if absent or unreadable."""
    try:
        raw = CREDENTIALS_PATH.read_text()
    except OSError:
        return None
    try:
        data = json.loads(raw)
    except ValueError:
        return None
    if not isinstance(data, dict) or not data.get("api_key"):
        return None
    return {
        "api_key": data["api_key"],
        "email": data.get("email", ""),
        "base_url": data.get("base_url", ""),
    }


def read_api_key() -> str | None:
    """Return just the stored API key, for `_cloud.py`'s resolution chain."""
    credentials = read_credentials()
    return credentials["api_key"] if credentials else None


def write_credentials(*, api_key: str, email: str, base_url: str) -> None:
    """Persist credentials at 0600, replacing anything already stored."""
    CREDENTIALS_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps({"api_key": api_key, "email": email, "base_url": base_url}, indent=2)
    fd = os.open(CREDENTIALS_PATH, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as handle:
        handle.write(payload)


def delete_credentials() -> bool:
    """Remove stored credentials. Returns False if there were none."""
    try:
        CREDENTIALS_PATH.unlink()
        return True
    except FileNotFoundError:
        return False
