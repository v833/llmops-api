from flask_wtf import FlaskForm
from langchain_core.load.dump import default
from wtforms import StringField, ValidationError
from wtforms.validators import DataRequired, URL, Length
from .schema import ListField
from marshmallow import Schema, fields, pre_dump
from internal.model.api_tool import ApiToolProvider, ApiTool


class ValidateOpenAPISchemaReq(FlaskForm):
    """验证OpenAPI插件规范"""

    openapi_schema = StringField(
        "openpai_schema", validators=[DataRequired(message="openapi_schema是必填的")]
    )


class CreateApiToolReq(FlaskForm):
    """创建自定义API工具请求"""

    name = StringField(
        "name",
        validators=[
            DataRequired(message="工具提供者名字不能为空"),
            Length(min=1, max=30, message="工具提供者的名字长度在1-30"),
        ],
    )
    icon = StringField(
        "icon",
        validators=[
            DataRequired(message="工具提供者的图标不能为空"),
            URL(message="工具提供者的图标必须是URL链接"),
        ],
    )
    openapi_schema = StringField(
        "openapi_schema",
        validators=[DataRequired(message="openapi_schema字符串不能为空")],
    )
    headers = ListField("headers", default=[])

    @classmethod
    def validate_headers(cls, form, field):
        """校验headers请求的数据是否正确，涵盖列表校验，列表元素校验"""
        for header in field.data:
            if not isinstance(header, dict):
                raise ValidationError("headers里的每一个元素都必须是字典")
            if set(header.keys()) != {"key", "value"}:
                raise ValidationError(
                    "headers里的每一个元素都必须包含key/value两个属性，不允许有其他属性"
                )


class GetApiToolProviderResp(Schema):
    """获取自定义API工具提供者信息响应"""

    id = fields.UUID()
    name = fields.String()
    icon = fields.String()
    openapi_schema = fields.String()
    headers = fields.List(fields.Dict, default=[])
    create_at = fields.Integer(default=0)

    @pre_dump
    def process_data(self, data: ApiToolProvider, **kwargs):
        return {
            "id": data.id,
            "name": data.name,
            "icon": data.icon,
            "openapi_schema": data.openapi_schema,
            "headers": data.headers,
            "created_at": int(data.created_at.timestamp()),
        }


class GetApiToolResp(Schema):
    id = fields.UUID()
    name = fields.String()
    description = fields.String()
    inputs = fields.List(fields.Dict, default=[])
    provider = fields.Dict()

    @pre_dump
    def process_data(self, data: ApiTool, **kwargs):
        provider = data.provider
        return {
            "id": data.id,
            "name": data.name,
            "description": data.description,
            "inputs": [
                {k: v for k, v in parameter.items() if k != "in"}
                for parameter in data.parameters
            ],
            "provider": {
                "id": provider.id,
                "name": provider.name,
                "icon": provider.icon,
                "description": provider.description,
                "headers": provider.headers,
            },
        }
