from injector import inject
from dataclasses import dataclass
import json
from internal.core.tools.api_tools.entites.openapi_schema import OpenAPISchema
from internal.core.tools.api_tools.providers.api_provider_manager import (
    ApiProviderManager,
)
from internal.exception import ValidateErrorException, NotFoundException
from uuid import UUID
from internal.model import ApiToolProvider, ApiTool
from internal.schema.api_tool_schma import (
    CreateApiToolReq,
    GetApiToolProvidersWithPageReq,
    UpdateApiToolProviderReq,
)
from sqlalchemy import desc
from .base_service import BaseService
from pkg.sqlalchemy import SQLAlchemy
from pkg.paginator import Paginator

account_id = "f47ac10b-58cc-4372-a567-0e02b2c3d479"


@inject
@dataclass
class ApiToolService(BaseService):
    """自定义API插件服务"""

    db: SQLAlchemy
    api_provider_manager: ApiProviderManager

    def get_api_tool(self, provider_id: UUID, tool_name: str):
        """根据传递的provider_id+tool_name获取对应工具的参数详情信息"""
        # todo:等待授权认证模块完成进行切换调整

        api_tool = (
            self.db.session.query(ApiTool)
            .filter_by(
                provider_id=provider_id,
                name=tool_name,
            )
            .one_or_none()
        )

        if api_tool is None or str(api_tool.account_id) != account_id:
            raise NotFoundException("该工具不存在")

        return api_tool

    def get_api_tool_providers_with_page(self, req: GetApiToolProvidersWithPageReq):
        """获取自定义API工具服务提供者分页列表数据"""
        # 1.构建分页查询器
        paginator = Paginator(db=self.db, req=req)

        # 2.构建筛选器
        filters = [ApiToolProvider.account_id == account_id]
        if req.search_word.data:
            filters.append(ApiToolProvider.name.ilike(f"%{req.search_word.data}%"))

        # 3.执行分页并获取数据
        api_tool_providers = paginator.paginate(
            self.db.session.query(ApiToolProvider)
            .filter(*filters)
            .order_by(desc("created_at"))
        )

        return api_tool_providers, paginator

    def get_api_tool_provider(self, provider_id: UUID):
        """根据传递的provider_id获取API工具提供者信息"""
        # todo:等待授权认证模块完成进行切换调整

        # 1.查询数据库获取对应的数据
        api_tool_provider = self.get(ApiToolProvider, provider_id)

        # 2.检验数据是否为空，并且判断该数据是否属于当前账号
        if api_tool_provider is None or str(api_tool_provider.account_id) != account_id:
            raise NotFoundException("该工具提供者不存在")

        return api_tool_provider

    def create_api_tool(self, req: CreateApiToolReq):
        """创建自定义API工具"""

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

    def delete_api_tool_provider(self, provider_id: UUID):
        """根据传递的provider_id删除对应的工具提供商+工具的所有信息"""

        # 1.先查找数据，检测下provider_id对应的数据是否存在，权限是否正确
        api_tool_provider = self.get(ApiToolProvider, provider_id)
        if api_tool_provider is None or str(api_tool_provider.account_id) != account_id:
            raise NotFoundException("该工具提供者不存在")

        # 2.开启数据库的自动提交
        with self.db.auto_commit():
            # 3.先来删除提供者对应的工具信息
            self.db.session.query(ApiTool).filter(
                ApiTool.provider_id == provider_id,
                ApiTool.account_id == account_id,
            ).delete()

            # 4.删除服务提供者
            self.db.session.delete(api_tool_provider)

    def update_api_tool_provider(
        self, provider_id: UUID, req: UpdateApiToolProviderReq
    ):
        """根据传递的provider_id更新对应的工具提供商+工具的所有信息"""
        # 1.先查找数据，检测下provider_id对应的数据是否存在，权限是否正确
        api_tool_provider = self.get(ApiToolProvider, provider_id)

        if api_tool_provider is None or str(api_tool_provider.account_id) != account_id:
            raise NotFoundException("该工具提供者不存在")

        openapi_schema = self.parse_openapi_schema(req.openapi_schema.data)

        check_api_tool_provider = (
            self.db.session.query(ApiToolProvider)
            .filter(
                ApiToolProvider.account_id == account_id,
                ApiToolProvider.name == req.name.data,
                ApiToolProvider.id != provider_id,
            )
            .one_or_none()
        )

        if check_api_tool_provider:
            raise ValidateErrorException(f"该工具提供者名字{req.name.data}已存在")

        with self.db.auto_commit():
            self.db.session.query(ApiTool).filter(
                ApiTool.provider_id == provider_id,
                ApiTool.account_id == account_id,
            ).delete()

        self.update(
            api_tool_provider,
            name=req.name.data,
            icon=req.icon.data,
            headers=req.headers.data,
            openapi_schema=req.openapi_schema.data,
        )

        # 7.新增工具信息从而完成覆盖更新
        for path, path_item in openapi_schema.paths.items():
            for method, method_item in path_item.items():
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

    def api_tool_invoke(self):
        provider_id = "634fdfb2-9614-4138-97b4-c1040d1c4ab4"
        tool_name = "YoudaoSuggest"
        api_tool = (
            self.db.session.query(ApiTool)
            .filter(
                ApiTool.provider_id == provider_id,
                ApiTool.name == tool_name,
            )
            .one_or_none()
        )
        api_tool_provider = api_tool.provider

        from internal.core.tools.api_tools.entites.tool_entity import ToolEntity

        tool = self.api_provider_manager.get_tool(
            ToolEntity(
                id=provider_id,
                name=tool_name,
                url=api_tool.url,
                method=api_tool.method,
                description=api_tool.description,
                headers=api_tool_provider.headers,
                parameters=api_tool.parameters,
            )
        )
        return tool.invoke({"q": "love", "doctype": "json"})

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
