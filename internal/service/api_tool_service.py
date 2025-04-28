from injector import inject
from dataclasses import dataclass
import json
from internal.core.tools.api_tools.entites.openai_schema import OpenAPISchema
from internal.exception import ValidateErrorException


@inject
@dataclass
class ApiToolService:
    """自定义API插件服务"""

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
