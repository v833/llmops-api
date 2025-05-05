from flask_wtf import FlaskForm
from marshmallow import Schema, fields, pre_dump
from wtforms import FloatField, IntegerField, StringField
from wtforms.validators import AnyOf, DataRequired, Length, URL, NumberRange, Optional
from internal.lib.helper import datetime_to_timestamp
from internal.entity.dataset_entity import RetrievalStrategy
from internal.model import Dataset, DatasetQuery
from pkg.paginator import PaginatorReq


class HitReq(FlaskForm):
    """知识库召回测试请求"""

    query = StringField(
        "query",
        validators=[
            DataRequired("查询内容不能为空"),
            Length(max=200, message="查询内容长度不能超过200字符"),
        ],
    )

    retrieval_strategy = StringField(
        "retrieval_strategy",
        validators=[
            DataRequired("检索策略不能为空"),
            AnyOf(
                [item.value for item in RetrievalStrategy],
                message="检索策略必须是以下值之一: %s"
                % [item.value for item in RetrievalStrategy],
            ),
        ],
    )

    k = IntegerField(
        "k",
        validators=[
            DataRequired("最大召回数量不能为空"),
            NumberRange(min=1, max=10, message="最大召回数量必须在1-10之间"),
        ],
    )

    score = FloatField(
        "score",
        validators=[
            NumberRange(min=0, max=0.99, message="最小得分必须在0-0.99之间"),
        ],
    )


class CreateDatasetReq(FlaskForm):
    """创建知识库请求"""

    name = StringField(
        "name",
        validators=[
            DataRequired("知识库名称不能为空"),
            Length(max=100, message="知识库名称长度不能超过100字符"),
        ],
    )
    icon = StringField(
        "icon",
        validators=[
            DataRequired("知识库图标不能为空"),
            URL("知识库图标必须是图片URL地址"),
        ],
    )
    description = StringField(
        "description",
        default="",
        validators=[
            Optional(),
            Length(max=2000, message="知识库描述长度不能超过2000字符"),
        ],
    )


class GetDatasetResp(Schema):
    """获取知识库详情响应结构"""

    id = fields.UUID(dump_default="")
    name = fields.String(dump_default="")
    icon = fields.String(dump_default="")
    description = fields.String(dump_default="")
    document_count = fields.Integer(dump_default=0)
    hit_count = fields.Integer(dump_default=0)
    related_app_count = fields.Integer(dump_default=0)
    character_count = fields.Integer(dump_default=0)
    updated_at = fields.Integer(dump_default=0)
    created_at = fields.Integer(dump_default=0)

    @pre_dump
    def process_data(self, data: Dataset, **kwargs):
        return {
            "id": data.id,
            "name": data.name,
            "icon": data.icon,
            "description": data.description,
            "document_count": data.document_count,
            "hit_count": data.hit_count,
            "related_app_count": data.related_app_count,
            "character_count": data.character_count,
            "updated_at": int(data.updated_at.timestamp()),
            "created_at": int(data.created_at.timestamp()),
        }


class UpdateDatasetReq(FlaskForm):
    """更新知识库请求"""

    name = StringField(
        "name",
        validators=[
            DataRequired("知识库名称不能为空"),
            Length(max=100, message="知识库名称长度不能超过100字符"),
        ],
    )
    icon = StringField(
        "icon",
        validators=[
            DataRequired("知识库图标不能为空"),
            URL("知识库图标必须是图片URL地址"),
        ],
    )
    description = StringField(
        "description",
        default="",
        validators=[
            Optional(),
            Length(max=2000, message="知识库描述长度不能超过2000字符"),
        ],
    )


class GetDatasetsWithPageReq(PaginatorReq):
    """获取知识库分页列表请求数据"""

    search_word = StringField(
        "search_word",
        default="",
        validators=[
            Optional(),
        ],
    )


class GetDatasetsWithPageResp(Schema):
    """获取知识库分页列表响应数据"""

    id = fields.UUID(dump_default="")
    name = fields.String(dump_default="")
    icon = fields.String(dump_default="")
    description = fields.String(dump_default="")
    document_count = fields.Integer(dump_default=0)
    related_app_count = fields.Integer(dump_default=0)
    character_count = fields.Integer(dump_default=0)
    updated_at = fields.Integer(dump_default=0)
    created_at = fields.Integer(dump_default=0)

    @pre_dump
    def process_data(self, data: Dataset, **kwargs):
        return {
            "id": data.id,
            "name": data.name,
            "icon": data.icon,
            "description": data.description,
            "document_count": data.document_count,
            "related_app_count": data.related_app_count,
            "character_count": data.character_count,
            "updated_at": int(data.updated_at.timestamp()),
            "created_at": int(data.created_at.timestamp()),
        }


class GetDatasetQueriesResp(Schema):
    """获取知识库最近查询响应结构"""

    id = fields.UUID(dump_default="")
    dataset_id = fields.UUID(dump_default="")
    query = fields.String(dump_default="")
    source = fields.String(dump_default="")
    created_at = fields.Integer(dump_default=0)

    @pre_dump
    def process_data(self, data: DatasetQuery, **kwargs):
        return {
            "id": data.id,
            "dataset_id": data.dataset_id,
            "query": data.query,
            "source": data.source,
            "created_at": datetime_to_timestamp(data.created_at),
        }
