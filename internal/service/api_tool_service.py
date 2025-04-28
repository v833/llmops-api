from injector import inject
from dataclasses import dataclass
import json
from internal.core.tools.api_tools.entites.openapi_schema import OpenAPISchema
from internal.exception import ValidateErrorException
from internal.model import ApiToolProvider, ApiTool
from internal.schema.api_tool_schma import CreateApiToolReq
from .base_service import BaseService
from pkg.sqlalchemy import SQLAlchemy


@inject
@dataclass
class ApiToolService(BaseService):
    """自定义API插件服务"""

    db: SQLAlchemy

    def create_api_tool(self, req: CreateApiToolReq):
        """创建自定义API工具"""
        account_id = "f47ac10b-58cc-4372-a567-0e02b2c3d479"

        openapi_schema = self.parse_openapi_schema(req.openapi_schema.data)

        api_tool_provider = (
            self.db.session.query(ApiToolProvider)
            .filter_by(
                account_id=account_id,
                name=req.name.data,
            )
            .one_or_none()
        )

        if api_tool_provider:
            raise ValidateErrorException(f"该工具提供者名字{req.name.data}已存在")

        api_tool_provider = self.create(
            ApiToolProvider,
            account_id=account_id,
            name=req.name.data,
            icon=req.icon.data,
            description=openapi_schema.description,
            openapi_schema=req.openapi_schema.data,
            headers=req.headers.data,
        )
        for path, path_items in openapi_schema.paths.items():
            for method, method_item in path_items.items():
                self.create(
                    ApiTool,
                    account_id=account_id,
                    provider_id=api_tool_provider.id,
                    name=method_item.get("operationId"),
                    description=method_item.get("description"),
                    url=f"{openapi_schema.server}{path}",
                    method=method,
                    parameters=method_item.get("parameters", []),
                )
        pass

    @classmethod
    def parse_openapi_schema(cls, openapi_schema_str: str) -> OpenAPISchema:
        """解析OpenAI API插件规范"""
        try:
            data = json.loads(openapi_schema_str.strip())
            if not isinstance(data, dict):
                raise
        except:
            raise ValidateErrorException("传递数据必须符合OpenAPI规范的JSON字符串")

        return OpenAPISchema(**data)
