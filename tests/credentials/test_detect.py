# Copyright 2026 Celesto AI
# Licensed under the Apache License, Version 2.0
"""Isolated table test for the shared secret detector (D-12).

The end-to-end tests prove each refusal path with one or two secrets. This
table exists because the detector's mistakes live in its patterns, which the
end-to-end tests cannot sweep cheaply. Failure modes written before the code:

False negatives (a secret slips into the sandbox):
1. Lower-case or mixed-case names (``openai_api_key``) skip the name rules.
2. Bare names (``TOKEN``, ``SECRET``, ``API_KEY``) skip ``*_TOKEN`` style rules.
3. Known value shapes under a harmless name: ``sk-``/``sk-proj-``/
   ``sk-ant-``, ``ghp_``/``gho_``/``ghs_``/``ghu_``/``ghr_``, ``github_pat_``,
   Slack ``xox?-``, ``AKIA``/``ASIA`` access key IDs, and JWTs.
4. Surrounding whitespace or a ``Bearer `` prefix hides the shape.

False positives (harmless config refused):
5. ``*_KEY_PATH`` / ``*_TOKEN_URL`` style names are refused because the name
   only contains ``_KEY``.
6. Names that merely start with or contain ``TOKEN``/``KEY`` as a word
   fragment (``TOKENIZERS_PARALLELISM``, ``KEYBOARD``) are refused.
7. Short look-alikes (``sk-learn``, ``AKIA`` in prose) trip the value rules.
8. Dotted version strings or hostnames look like JWTs.
9. An empty value under a secret-looking name is refused although nothing
   secret would enter the sandbox.
"""

from __future__ import annotations

import pytest

from celesto.credentials.detect import looks_like_secret

# Sentinel values only; none of these are real credentials.
_JWT = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ3NC10ZXN0In0.c2VudGluZWwtc2lnbmF0dXJl"

SECRETS = [
    # (1) case
    ("openai_api_key", "x"),
    ("Github_Token", "x"),
    # (2) bare names
    ("TOKEN", "x"),
    ("SECRET", "x"),
    ("API_KEY", "x"),
    ("DB_PASSWORD", "x"),
    ("PASSWORD", "x"),
    ("AWS_CREDENTIALS", "x"),
    ("MY_CREDENTIAL_FILE", "x"),
    ("CLIENT_SECRET", "x"),
    # (3) value shapes under harmless names
    ("FOO", "sk-w4sentinel0000000000000000"),
    ("FOO", "sk-proj-w4sentinel000000000000000"),
    ("FOO", "sk-ant-api03-w4sentinel00000000000"),
    ("FOO", "ghp_w4sentinel0000000000000000000000"),
    ("FOO", "gho_w4sentinel0000000000000000000000"),
    ("FOO", "ghs_w4sentinel0000000000000000000000"),
    ("FOO", "github_pat_w4sentinel000000000000000"),
    ("FOO", "xoxb-1234-5678-w4sentinel"),
    ("FOO", "xoxp-1234-5678-w4sentinel"),
    ("FOO", "AKIAW4SENTINEL000000"),
    ("FOO", "ASIAW4SENTINEL000000"),
    ("FOO", _JWT),
    # (4) wrapping
    ("FOO", "  sk-w4sentinel0000000000000000\n"),
    ("AUTH_HEADER", "Bearer ghp_w4sentinel0000000000000000000000"),
]

NOT_SECRETS = [
    # (5) suffix rules must anchor at the end of the name
    ("PUBLIC_KEY_PATH", "/root/.ssh/id_ed25519.pub"),
    ("SSH_KEY_PATH", "/root/.ssh/id_ed25519"),
    ("TOKEN_URL", "https://auth.example.com/token"),
    ("KEYS_DIR", "/etc/keys"),
    # (6) word fragments
    ("TOKENIZERS_PARALLELISM", "false"),
    ("KEYBOARD", "us"),
    ("SECRETARY", "alice"),
    # (7) short look-alikes
    ("MODEL", "sk-learn"),
    ("NOTE", "AKIA is a prefix"),
    ("PREFIX", "xox"),
    ("NAME", "github_pat"),
    # (8) dotted values
    ("VERSION", "1.2.3"),
    ("HOST", "api.openai.com"),
    ("CALLBACK", "eyJ.eyJ.x"),
    # plain config
    ("PATH", "/usr/local/bin:/usr/bin"),
    ("DEBUG", "1"),
    ("NODE_ENV", "production"),
    # (9) empty value under a secret name carries nothing
    ("OPENAI_API_KEY", ""),
]


@pytest.mark.parametrize(("name", "value"), SECRETS)
def test_detects_secret(name: str, value: str) -> None:
    assert looks_like_secret(name, value) is True


@pytest.mark.parametrize(("name", "value"), NOT_SECRETS)
def test_allows_non_secret(name: str, value: str) -> None:
    assert looks_like_secret(name, value) is False
