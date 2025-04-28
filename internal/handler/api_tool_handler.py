from injector import inject
from dataclasses import dataclass
from internal.core.tools.api_tools.entites import openai_schema
from internal.service import ApiToolService
from internal.schema.api_tool_schma import ValidateOpenAPISchemaReq
from pkg.response import validate_error_json, success_message, success_json
import json


@inject
@dataclass
class ApiToolHandler:
    """自定义API插件处理器"""

    api_tool_service: ApiToolService

    def validate_openapi_schema(self):
        """验证OpenAI API插件规范"""
        req = ValidateOpenAPISchemaReq()

        if not req.validate():
            return validate_error_json(req.errors)

        openapi_schema = self.api_tool_service.parse_openapi_schema(
            req.openapi_schema.data
        )

        return success_json(openapi_schema.model_dump())
