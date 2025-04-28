from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired


class ValidateOpenAPISchemaReq(FlaskForm):
    """验证OpenAPI插件规范"""

    openapi_schema = StringField(
        "openpai_schema", validators=[DataRequired(message="openapi_schema是必填的")]
    )
