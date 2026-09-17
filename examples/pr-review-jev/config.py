"""Resolve provider credentials without silently switching providers during a review."""

import os


def llm_config(env=None):
    env = os.environ if env is None else env
    provider = env.get("LLM_PROVIDER") or (
        "custom" if env.get("LLM_BASE_URL") else "openai" if env.get("OPENAI_API_KEY") else "gateway"
    )
    if provider == "openai":
        base, key, default = "https://api.openai.com/v1", env.get("OPENAI_API_KEY"), "gpt-5.6-luna"
        key_name = "OPENAI_API_KEY"
    elif provider == "gateway":
        base, key, default = (
            "https://ai-gateway.vercel.sh/v1",
            env.get("AI_GATEWAY_API_KEY"),
            "openai/gpt-5.6-luna",
        )
        key_name = "AI_GATEWAY_API_KEY"
    elif provider == "custom":
        base, key, default = env.get("LLM_BASE_URL"), env.get("LLM_API_KEY"), None
        key_name = "LLM_API_KEY"
        if not base:
            raise ValueError("Set LLM_BASE_URL for the custom provider.")
    else:
        raise ValueError("Set LLM_PROVIDER to openai, gateway, or custom.")
    if not key:
        raise ValueError(f"Set {key_name} in .env, then restart the server.")
    models = {role: env.get(role + "_MODEL") or default for role in ("INVESTIGATOR", "EVALUATOR")}
    models["WRITER"] = env.get("WRITER_MODEL") or models["INVESTIGATOR"]
    if not all(models.values()):
        raise ValueError("Set INVESTIGATOR_MODEL and EVALUATOR_MODEL for the custom provider.")
    return {"provider": provider, "base_url": base, "api_key": key, "models": models}


def model_for(role):
    return llm_config()["models"][role]


def jev_provider(env=None):
    env = os.environ if env is None else env
    provider = env.get("JEV_PROVIDER") or ("gateway" if env.get("AI_GATEWAY_API_KEY") else "typesafe")
    if provider not in {"gateway", "typesafe"}:
        raise ValueError("Set JEV_PROVIDER to gateway or typesafe.")
    key = "AI_GATEWAY_API_KEY" if provider == "gateway" else "TYPESAFE_API_KEY"
    if not env.get(key):
        raise ValueError(f"Set {key} in .env, then restart the server.")
    return provider
