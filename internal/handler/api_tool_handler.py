from uuid import UUID
from injector import inject
from dataclasses import dataclass
from internal.core.tools.api_tools.entites import openapi_schema
from internal.service import ApiToolService
from internal.schema.api_tool_schma import (
    ValidateOpenAPISchemaReq,
    CreateApiToolReq,
    GetApiToolProviderResp,
    GetApiToolResp,
    GetApiToolProvidersWithPageReq,
    GetApiToolProvidersWithPageResp,
)
from flask import request
from pkg.response import validate_error_json, success_message, success_json
from pkg.paginator import PageModel


@inject
@dataclass
class ApiToolHandler:
    """自定义API插件处理器"""

    api_tool_service: ApiToolService

    def get_api_tool_providers_with_page(self):
        """获取API工具提供者列表信息，该接口支持分页"""
        req = GetApiToolProvidersWithPageReq(request.args)
        if not req.validate():
            return validate_error_json(req.errors)

        api_tool_providers, paginator = (
            self.api_tool_service.get_api_tool_providers_with_page(req)
        )

        resp = GetApiToolProvidersWithPageResp(many=True)

        return success_json(
            PageModel(list=resp.dump(api_tool_providers), paginator=paginator)
        )

    def create_api_tool_provider(self):
        """创建自定义API工具"""
        req = CreateApiToolReq()
        if not req.validate():
            return validate_error_json(req.errors)

        self.api_tool_service.create_api_tool(req)

        return success_message("创建自定义API插件成功")

    def get_api_tool(self, provider_id: UUID, tool_name: str):

        api_tool = self.api_tool_service.get_api_tool(provider_id, tool_name)

        resp = GetApiToolResp()

        return success_json(resp.dump(api_tool))

    def get_api_tool_provider(self, provider_id: UUID):
        api_tool_provider = self.api_tool_service.get_api_tool_provider(provider_id)

        resp = GetApiToolProviderResp()

        return success_json(resp.dump(api_tool_provider))

    def delete_api_tool_provider(self, provider_id: UUID):
        """删除自定义API工具"""
        self.api_tool_service.delete_api_tool_provider(provider_id)
        return success_message("删除自定义API插件成功")

    def validate_openapi_schema(self):
        """验证OpenAI API插件规范"""
        req = ValidateOpenAPISchemaReq()

        if not req.validate():
            return validate_error_json(req.errors)

        openapi_schema = self.api_tool_service.parse_openapi_schema(
            req.openapi_schema.data
        )

        return success_json(openapi_schema.model_dump(), message="验证成功")
