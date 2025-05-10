import json
import uuid
import os
from uuid import UUID
from typing import Generator
from dataclasses import dataclass
from injector import inject
from langchain_core.memory import BaseMemory
from langchain_core.runnables import RunnablePassthrough, RunnableLambda, RunnableConfig
from langchain_core.tracers import Run
from langchain_openai import ChatOpenAI
from langgraph.constants import END
from redis import Redis

from flask import request
from internal.core.agent.agents import FunctionCallAgent
from internal.core.agent.entities import AgentConfig
from internal.core.agent.agents.agent_queue_manager import AgentQueueManager
from internal.core.tools.builtin_tools.providers import BuiltinProviderManager
from internal.schema.app_schema import CompletionReq
from internal.service import (
    AppService,
    VectorDatabaseService,
    ApiToolService,
)
from internal.entity.conversation_entity import InvokeFrom
from internal.service.conversation_service import ConversationService

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
    def get_draft_app_config(self, app_id: UUID):
        """根据传递的应用id获取应用的最新草稿配置"""
        pass

    @login_required
    def update_draft_app_config(self, app_id: UUID):
        """根据传递的应用id+草稿配置更新应用的最新草稿配置"""
        pass

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
        # 1.提取从接口中获取的输入，POST
        req = CompletionReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 2.定义工具列表
        tools = [
            self.builtin_provider_manager.get_tool("google", "google_serper")(),
            self.builtin_provider_manager.get_tool("gaode", "gaode_weather")(),
            self.builtin_provider_manager.get_tool("dalle", "dalle3")(),
        ]

        agent = FunctionCallAgent(
            AgentConfig(
                llm=ChatOpenAI(
                    model=os.getenv("OPENAI_MODEL"), api_key=os.getenv("OPENAI_API_KEY")
                ),
                enable_long_term_memory=True,
                tools=tools,
            ),
            AgentQueueManager(
                user_id=uuid.uuid4(),
                task_id=uuid.uuid4(),
                invoke_from=InvokeFrom.DEBUGGER,
                redis_client=self.redis_client,
            ),
        )

        def stream_event_response() -> Generator:
            """流式事件输出响应"""
            for agent_queue_event in agent.run(req.query.data, [], "用户介绍自己叫wq"):
                data = {
                    "id": str(agent_queue_event.id),
                    "task_id": str(agent_queue_event.task_id),
                    "event": agent_queue_event.event,
                    "thought": agent_queue_event.thought,
                    "observation": agent_queue_event.observation,
                    "tool": agent_queue_event.tool,
                    "tool_input": agent_queue_event.tool_input,
                    "answer": agent_queue_event.answer,
                    "latency": agent_queue_event.latency,
                }
                yield f"event: {agent_queue_event.event}\ndata: {json.dumps(data)}\n\n"

        return compact_generate_response(stream_event_response())

    def ping(self):
        from internal.core.agent.agents import FunctionCallAgent
        from internal.core.agent.entities import AgentConfig
        from langchain_openai import ChatOpenAI

        agent = FunctionCallAgent(
            AgentConfig(
                llm=ChatOpenAI(
                    model=os.getenv("OPENAI_MODEL"), api_key=os.getenv("OPENAI_API_KEY")
                ),
                preset_prompt="你是一个诗人,请根据用户输入的主题,创建一首诗",
            )
        )

        state = agent.run("程序员", history=[], long_term_memory="")

        content = state["messages"][-1].content

        return success_json({"content": content})
