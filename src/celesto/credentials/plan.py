# Copyright 2026 Celesto AI
# Licensed under the Apache License, Version 2.0
"""Turn a computer's user secrets into a per-start :class:`CredentialPlan`.

``build_plan`` runs at every computer start (``celesto computer start``, SDK
``start()``) and when the first secret is set on a running computer. It
re-reads every real value from its source on the host (D-09), reuses each
secret's stored placeholder so the guest stays stable across restarts, and
returns everything the runtime needs: bindings for the proxy, placeholder env
vars for the guest, and warnings for secrets whose value was not available.
Real values live only in ``plan.real_values`` and go to the proxy over its
private channel.

Only user secrets (``celesto computer secret set``) feed the plan (D-20).
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Any

from celesto.credentials import user_secrets
from celesto.credentials.types import CredentialPlan


def build_plan(
    sandbox_id: str,
    state: Any,
    env: Mapping[str, str] | None = None,
) -> CredentialPlan:
    """Return the credential plan for one start of *sandbox_id*.

    Args:
        sandbox_id: Computer name; used for placeholders and warnings.
        state: The host state manager holding the computer's secrets.
        env: Env of the command starting the computer (default ``os.environ``).
    """
    env = os.environ if env is None else env
    plan = CredentialPlan()
    if state is not None:
        bindings, guest_env, missing = user_secrets.plan_for(sandbox_id, state, environ=env)
        for binding in bindings:
            plan.bindings.append(binding)
            real = user_secrets.resolve(binding.source, env)
            if real:
                plan.real_values[binding.name] = real
        plan.guest_env.update(guest_env)
        plan.missing.extend(missing)
    _LAST_PLANS[sandbox_id] = plan
    return plan


_LAST_PLANS: dict[str, CredentialPlan] = {}
"""The latest plan per computer in this process, until :func:`take_last_plan`.

Lets the start path report missing-secret warnings for what ``facade.start``
attached without building the plan a second time. Never persisted.
"""


def take_last_plan(sandbox_id: str) -> CredentialPlan | None:
    """Return and forget the plan last built for *sandbox_id* in this process."""
    return _LAST_PLANS.pop(sandbox_id, None)


__all__ = ["build_plan", "take_last_plan"]
