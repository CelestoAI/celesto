"""Provider selection, performed once per public computer handle."""

from typing import Any, Literal

from celesto._providers.base import ComputerProvider

ProviderName = Literal["local", "cloud"]


def resolve_provider(
    provider: ProviderName | None, local: bool | None, fixed: ProviderName | None = None
) -> ProviderName:
    if provider is not None and provider not in ("local", "cloud"):
        raise ValueError("provider must be 'local' or 'cloud'.")
    if local is not None and not isinstance(local, bool):
        raise ValueError("local must be True or False.")
    legacy: ProviderName | None = ("local" if local else "cloud") if local is not None else None
    if provider is not None and legacy is not None and provider != legacy:
        raise ValueError("provider and local select different locations; use provider only.")
    selected = provider or legacy or fixed or "local"
    if fixed is not None and selected != fixed:
        raise ValueError(f"This class only supports provider='{fixed}'.")
    return selected


def make_provider(name: ProviderName, options: dict[str, Any]) -> ComputerProvider:
    if name == "local":
        from celesto._providers.local import LocalProvider

        return LocalProvider(**options)
    from celesto._providers.cloud import CloudProvider

    return CloudProvider(**options)
