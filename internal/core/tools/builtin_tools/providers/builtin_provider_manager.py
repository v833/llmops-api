from injector import inject, singleton
from typing import Any, List
import os
from pydantic import Field
import yaml

from internal.core.tools.builtin_tools.entities.provider_entity import (
    Provider,
    ProviderEntity,
)


@inject
@singleton
class BuiltinProviderManager:
    provider_map: dict[str, Provider] = {}

    def __init__(self):
        self._get_provider_map()

    def get_provider(self, provider_name: str) -> Provider:
        """根据服务提供商的名字，来获取到该服务提供商的对象"""
        return self.provider_map.get(provider_name)

    def get_proivders(self) -> List[Provider]:
        """获取所有的服务提供商对象"""
        return list(self.provider_map.values())

    def get_provider_entites(self) -> List[ProviderEntity]:
        """获取所有的服务提供商实体/信息列表"""
        return [provider.provider_entity for provider in self.provider_map.values()]

    def get_tool(self, provider_name: str, tool_name: str) -> Any:
        """根据服务提供商的名字和工具的名字，来获取到该服务提供商下的指定工具"""
        provider = self.get_provider(provider_name)
        if provider:
            return provider.get_tool(tool_name)
        return None

    def _get_provider_map(self):
        if self.provider_map:
            return

        current_path = os.path.abspath(__file__)
        provider_path = os.path.dirname(current_path)
        providers_yaml_path = os.path.join(provider_path, "providers.yaml")

        with open(providers_yaml_path, "r", encoding="utf-8") as f:
            providers_yaml_data = yaml.safe_load(f)

        for idx, provider_data in enumerate(providers_yaml_data):
            provider_entity = ProviderEntity(**provider_data)
            self.provider_map[provider_entity.name] = Provider(
                name=provider_entity.name,
                position=idx + 1,
                provider_entity=provider_entity,
            )
