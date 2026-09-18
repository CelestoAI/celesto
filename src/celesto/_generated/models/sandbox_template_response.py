from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast


T = TypeVar("T", bound="SandboxTemplateResponse")


@_attrs_define
class SandboxTemplateResponse:
    """User-facing sandbox template option.

    Attributes:
        id (str):
        display_name (str):
        description (str):
        default_vcpus (int):
        default_ram_mb (int):
        default_disk_size_mb (int):
        aliases (list[str] | Unset):
        capabilities (list[str] | Unset):
        preinstalled_tools (list[str] | Unset):
        recommended_for (list[str] | Unset):
        default_published_ports (list[int] | Unset):
        has_playwright_browsers (bool | Unset):  Default: False.
        has_browser_system_deps (bool | Unset):  Default: False.
        version (None | str | Unset):
        experimental (bool | Unset):  Default: False.
    """

    id: str
    display_name: str
    description: str
    default_vcpus: int
    default_ram_mb: int
    default_disk_size_mb: int
    aliases: list[str] | Unset = UNSET
    capabilities: list[str] | Unset = UNSET
    preinstalled_tools: list[str] | Unset = UNSET
    recommended_for: list[str] | Unset = UNSET
    default_published_ports: list[int] | Unset = UNSET
    has_playwright_browsers: bool | Unset = False
    has_browser_system_deps: bool | Unset = False
    version: None | str | Unset = UNSET
    experimental: bool | Unset = False
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        display_name = self.display_name

        description = self.description

        default_vcpus = self.default_vcpus

        default_ram_mb = self.default_ram_mb

        default_disk_size_mb = self.default_disk_size_mb

        aliases: list[str] | Unset = UNSET
        if not isinstance(self.aliases, Unset):
            aliases = self.aliases

        capabilities: list[str] | Unset = UNSET
        if not isinstance(self.capabilities, Unset):
            capabilities = self.capabilities

        preinstalled_tools: list[str] | Unset = UNSET
        if not isinstance(self.preinstalled_tools, Unset):
            preinstalled_tools = self.preinstalled_tools

        recommended_for: list[str] | Unset = UNSET
        if not isinstance(self.recommended_for, Unset):
            recommended_for = self.recommended_for

        default_published_ports: list[int] | Unset = UNSET
        if not isinstance(self.default_published_ports, Unset):
            default_published_ports = self.default_published_ports

        has_playwright_browsers = self.has_playwright_browsers

        has_browser_system_deps = self.has_browser_system_deps

        version: None | str | Unset
        if isinstance(self.version, Unset):
            version = UNSET
        else:
            version = self.version

        experimental = self.experimental

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "display_name": display_name,
                "description": description,
                "default_vcpus": default_vcpus,
                "default_ram_mb": default_ram_mb,
                "default_disk_size_mb": default_disk_size_mb,
            }
        )
        if aliases is not UNSET:
            field_dict["aliases"] = aliases
        if capabilities is not UNSET:
            field_dict["capabilities"] = capabilities
        if preinstalled_tools is not UNSET:
            field_dict["preinstalled_tools"] = preinstalled_tools
        if recommended_for is not UNSET:
            field_dict["recommended_for"] = recommended_for
        if default_published_ports is not UNSET:
            field_dict["default_published_ports"] = default_published_ports
        if has_playwright_browsers is not UNSET:
            field_dict["has_playwright_browsers"] = has_playwright_browsers
        if has_browser_system_deps is not UNSET:
            field_dict["has_browser_system_deps"] = has_browser_system_deps
        if version is not UNSET:
            field_dict["version"] = version
        if experimental is not UNSET:
            field_dict["experimental"] = experimental

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        display_name = d.pop("display_name")

        description = d.pop("description")

        default_vcpus = d.pop("default_vcpus")

        default_ram_mb = d.pop("default_ram_mb")

        default_disk_size_mb = d.pop("default_disk_size_mb")

        aliases = cast(list[str], d.pop("aliases", UNSET))

        capabilities = cast(list[str], d.pop("capabilities", UNSET))

        preinstalled_tools = cast(list[str], d.pop("preinstalled_tools", UNSET))

        recommended_for = cast(list[str], d.pop("recommended_for", UNSET))

        default_published_ports = cast(
            list[int], d.pop("default_published_ports", UNSET)
        )

        has_playwright_browsers = d.pop("has_playwright_browsers", UNSET)

        has_browser_system_deps = d.pop("has_browser_system_deps", UNSET)

        def _parse_version(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        version = _parse_version(d.pop("version", UNSET))

        experimental = d.pop("experimental", UNSET)

        sandbox_template_response = cls(
            id=id,
            display_name=display_name,
            description=description,
            default_vcpus=default_vcpus,
            default_ram_mb=default_ram_mb,
            default_disk_size_mb=default_disk_size_mb,
            aliases=aliases,
            capabilities=capabilities,
            preinstalled_tools=preinstalled_tools,
            recommended_for=recommended_for,
            default_published_ports=default_published_ports,
            has_playwright_browsers=has_playwright_browsers,
            has_browser_system_deps=has_browser_system_deps,
            version=version,
            experimental=experimental,
        )

        sandbox_template_response.additional_properties = d
        return sandbox_template_response

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
