from dataclasses import dataclass

from flask import Flask, Blueprint
from injector import inject

from internal.handler import AppHandler, BuiltinToolHandler, ApiToolHandler


@inject
@dataclass
class Router:
    """路由"""

    app_handler: AppHandler
    builtin_tool_handler: BuiltinToolHandler
    api_tool_handler: ApiToolHandler

    def register_router(self, app: Flask):
        """注册路由"""
        # 1.创建一个蓝图
        bp = Blueprint("llmops", __name__, url_prefix="")

        # 2.将url与对应的控制器方法做绑定
        bp.add_url_rule("/ping", view_func=self.app_handler.ping)
        bp.add_url_rule(
            "/apps/<uuid:app_id>/debug",
            methods=["POST", "OPTIONS"],
            view_func=self.app_handler.debug,
        )
        bp.add_url_rule(
            "/app", methods=["POST", "OPTIONS"], view_func=self.app_handler.create_app
        )
        bp.add_url_rule("/app", methods=["GET"], view_func=self.app_handler.get_all_app)
        bp.add_url_rule("/app/<uuid:id>", view_func=self.app_handler.get_app)
        bp.add_url_rule(
            "/app/<uuid:id>", methods=["POST"], view_func=self.app_handler.update_app
        )
        bp.add_url_rule(
            "/app/<uuid:id>/delete",
            methods=["POST"],
            view_func=self.app_handler.delete_app,
        )

        # 内置插件广场
        bp.add_url_rule(
            "/builtin-tools",
            methods=["GET"],
            view_func=self.builtin_tool_handler.get_builtin_tools,
        )

        bp.add_url_rule(
            "/builtin-tools/<string:provider_name>/tools/<string:tool_name>",
            methods=["GET"],
            view_func=self.builtin_tool_handler.get_provider_tool,
        )

        bp.add_url_rule(
            "/builtin-tools/<string:provider_name>/icon",
            view_func=self.builtin_tool_handler.get_provider_icon,
        )
        bp.add_url_rule(
            "/builtin-tools/categories",
            view_func=self.builtin_tool_handler.get_categories,
        )

        # 4.自定义API插件模块
        # bp.add_url_rule(
        #     "/api-tools",
        #     view_func=self.api_tool_handler.get_api_tool_provider,
        # )
        bp.add_url_rule(
            "/api-tools/validate-openapi-schema",
            methods=["POST"],
            view_func=self.api_tool_handler.validate_openapi_schema,
        )
        bp.add_url_rule(
            "/api-tools",
            methods=["POST"],
            view_func=self.api_tool_handler.create_api_tool_provider,
        )
        bp.add_url_rule(
            "/api-tools/<uuid:provider_id>",
            view_func=self.api_tool_handler.get_api_tool_provider,
        )
        # bp.add_url_rule(
        #     "/api-tools/<uuid:provider_id>",
        #     methods=["POST"],
        #     view_func=self.api_tool_handler.update_api_tool_provider,
        # )
        # bp.add_url_rule(
        #     "/api-tools/<uuid:provider_id>/tools/<string:tool_name>",
        #     view_func=self.api_tool_handler.get_api_tool,
        # )
        # bp.add_url_rule(
        #     "/api-tools/<uuid:provider_id>/delete",
        #     methods=["POST"],
        #     view_func=self.api_tool_handler.delete_api_tool_provider,
        # )

        # 在应用上去注册蓝图
        app.register_blueprint(bp)
