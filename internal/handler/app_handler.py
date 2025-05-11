import json
import uuid
from uuid import UUID
from dataclasses import dataclass
from injector import inject
from langchain_core.memory import BaseMemory
from langchain_core.runnables import RunnableConfig
from langchain_core.tracers import Run
from langgraph.constants import END
from redis import Redis

from flask import current_app, request
from internal.core.tools.builtin_tools.providers import BuiltinProviderManager
from internal.schema.app_schema import (
    DebugChatReq,
    FallbackHistoryToDraftReq,
    GetAppsWithPageReq,
    GetAppsWithPageResp,
    GetDebugConversationMessagesWithPageReq,
    GetDebugConversationMessagesWithPageResp,
    GetPublishHistoriesWithPageReq,
    GetPublishHistoriesWithPageResp,
    UpdateAppReq,
    UpdateDebugConversationSummaryReq,
)
from internal.service import (
    AppService,
    VectorDatabaseService,
    ApiToolService,
)
from internal.service.conversation_service import ConversationService

from internal.service.retrieval_service import RetrievalService
from pkg.paginator.paginator import PageModel
from pkg.response import (
    success_json,
    validate_error_json,
    success_message,
)
import dotenv
from flask_login import login_required, current_user
from pkg.response.response import compact_generate_response
from internal.schema.app_schema import CreateAppReq, GetAppResp

dotenv.load_dotenv()


@inject
@dataclass
class AppHandler:
    """应用控制器"""

    app_service: AppService
    api_tool_service: ApiToolService
    vector_database_service: VectorDatabaseService
    builtin_provider_manager: BuiltinProviderManager
    conversation_service: ConversationService
    redis_client: Redis
    retrieval_service: RetrievalService

    @login_required
    def create_app(self):
        """调用服务创建新的APP记录"""

        req = CreateAppReq()
        if not req.validate():
            return validate_error_json(req.errors)

        app = self.app_service.create_app(req, current_user)
        return success_json({"id": app.id})

    @login_required
    def get_app(self, app_id: uuid.UUID):
        """获取指定的应用基础信息"""
        app = self.app_service.get_app(app_id, current_user)
        resp = GetAppResp()
        return success_json(resp.dump(app))

    @login_required
    def update_app(self, app_id: UUID):
        """根据传递的信息更新指定的应用"""
        # 1.提取数据并校验
        req = UpdateAppReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 2.调用服务更新数据
        self.app_service.update_app(app_id, current_user, **req.data)

        return success_message("修改Agent智能体应用成功")

    @login_required
    def copy_app(self, app_id: UUID):
        """根据传递的应用id快速拷贝该应用"""
        app = self.app_service.copy_app(app_id, current_user)
        return success_json({"id": app.id})

    @login_required
    def delete_app(self, app_id: UUID):
        """根据传递的信息删除指定的应用"""
        self.app_service.delete_app(app_id, current_user)
        return success_message("删除Agent智能体应用成功")

    @login_required
    def get_apps_with_page(self):
        """获取当前登录账号的应用分页列表数据"""
        # 1.提取数据并校验
        req = GetAppsWithPageReq(request.args)
        if not req.validate():
            return validate_error_json(req.errors)

        # 2.调用服务获取列表数据以及分页器
        apps, paginator = self.app_service.get_apps_with_page(req, current_user)

        # 3.构建响应结构并返回
        resp = GetAppsWithPageResp(many=True)

        return success_json(PageModel(list=resp.dump(apps), paginator=paginator))

    @login_required
    def get_draft_app_config(self, app_id: UUID):
        """根据传递的应用id获取应用的最新草稿配置"""
        draft_config = self.app_service.get_draft_app_config(app_id, current_user)
        return success_json(draft_config)

    @login_required
    def update_draft_app_config(self, app_id: UUID):
        """根据传递的应用id+草稿配置更新应用的最新草稿配置"""
        # 1.获取草稿请求json数据
        draft_app_config = request.get_json(force=True, silent=True) or {}

        # 2.调用服务更新应用的草稿配置
        self.app_service.update_draft_app_config(app_id, draft_app_config, current_user)

        return success_message("更新应用草稿配置成功")

    @login_required
    def publish(self, app_id: UUID):
        """根据传递的应用id发布/更新特定的草稿配置信息"""
        self.app_service.publish_draft_app_config(app_id, current_user)
        return success_message("发布/更新应用配置成功")

    @login_required
    def cancel_publish(self, app_id: UUID):
        """根据传递的应用id，取消发布指定的应用配置信息"""
        self.app_service.cancel_publish_app_config(app_id, current_user)
        return success_message("取消发布应用配置成功")

    @login_required
    def fallback_history_to_draft(self, app_id: UUID):
        """根据传递的应用id+历史配置版本id，退回指定版本到草稿中"""
        # 1.提取数据并校验
        req = FallbackHistoryToDraftReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 2.调用服务回退指定版本到草稿
        self.app_service.fallback_history_to_draft(
            app_id, req.app_config_version_id.data, current_user
        )

        return success_message("回退历史配置至草稿成功")

    @login_required
    def get_publish_histories_with_page(self, app_id: UUID):
        """根据传递的应用id，获取应用发布历史列表"""
        # 1.获取请求数据并校验
        req = GetPublishHistoriesWithPageReq(request.args)
        if not req.validate():
            return validate_error_json(req.errors)

        # 2.调用服务获取分页列表数据
        app_config_versions, paginator = (
            self.app_service.get_publish_histories_with_page(app_id, req, current_user)
        )

        # 3.创建响应结构并返回
        resp = GetPublishHistoriesWithPageResp(many=True)

        return success_json(
            PageModel(list=resp.dump(app_config_versions), paginator=paginator)
        )

    @login_required
    def get_debug_conversation_summary(self, app_id: UUID):
        """根据传递的应用id获取调试会话长期记忆"""
        summary = self.app_service.get_debug_conversation_summary(app_id, current_user)
        return success_json({"summary": summary})

    @login_required
    def update_debug_conversation_summary(self, app_id: UUID):
        """根据传递的应用id+摘要信息更新调试会话长期记忆"""
        # 1.提取数据并校验
        req = UpdateDebugConversationSummaryReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 2.调用服务更新调试会话长期记忆
        self.app_service.update_debug_conversation_summary(
            app_id, req.summary.data, current_user
        )

        return success_message("更新AI应用长期记忆成功")

    @login_required
    def delete_debug_conversation(self, app_id: UUID):
        """根据传递的应用id，清空该应用的调试会话记录"""
        self.app_service.delete_debug_conversation(app_id, current_user)
        return success_message("清空应用调试会话记录成功")

    @login_required
    def debug_chat(self, app_id: UUID):
        """根据传递的应用id+query，发起调试对话"""
        # 1.提取数据并校验数据
        req = DebugChatReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 2.调用服务发起会话调试
        response = self.app_service.debug_chat(app_id, req.query.data, current_user)

        return compact_generate_response(response)

    @login_required
    def stop_debug_chat(self, app_id: UUID, task_id: UUID):
        """根据传递的应用id+任务id停止某个应用的指定调试会话"""
        self.app_service.stop_debug_chat(app_id, task_id, current_user)
        return success_message("停止应用调试会话成功")

    @login_required
    def get_debug_conversation_messages_with_page(self, app_id: UUID):
        """根据传递的应用id，获取该应用的调试会话分页列表记录"""
        # 1.提取请求并校验数据
        req = GetDebugConversationMessagesWithPageReq(request.args)
        if not req.validate():
            return validate_error_json(req.errors)

        # 2.调用服务获取数据
        messages, paginator = (
            self.app_service.get_debug_conversation_messages_with_page(
                app_id, req, current_user
            )
        )

        # 3.创建响应结构
        resp = GetDebugConversationMessagesWithPageResp(many=True)

        return success_json(PageModel(list=resp.dump(messages), paginator=paginator))

    @classmethod
    def _load_memory_variables(cls, inputs, config: RunnableConfig):
        configurable = config.get("configurable", {})
        configurable_memory = configurable.get("memory", None)
        if configurable_memory is not None and isinstance(
            configurable_memory, BaseMemory
        ):
            return configurable_memory.load_memory_variables(inputs)

        return {"history": []}

    @classmethod
    def _save_context(cls, run_obj: Run, config: RunnableConfig):
        configurable = config.get("configurable", {})
        configurable_memory = configurable.get("memory", None)
        if configurable_memory is not None and isinstance(
            configurable_memory, BaseMemory
        ):
            return configurable_memory.save_context(run_obj.inputs, run_obj.outputs)

        return None

    def debug(self, app_id: UUID):
        """应用会话调试聊天接口，该接口为流式事件输出"""
        pass

    def ping(self):
        from internal.core.workflow import Workflow
        from internal.core.workflow.entites.workflow_entity import WorkflowConfig

        workflow = Workflow(
            WorkflowConfig(
                name="test",
                description="test",
                nodes=[],
                edges=[],
            )
        )
        return success_message(workflow.invoke({"query": "hello"}))
