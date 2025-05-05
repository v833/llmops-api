import json
import uuid
import os
from dataclasses import dataclass
from operator import itemgetter
from queue import Queue
from threading import Thread
from injector import inject
from langchain.memory import ConversationBufferWindowMemory
from langchain_community.chat_message_histories import FileChatMessageHistory
from langchain_core.documents import Document
from langchain_core.memory import BaseMemory
from langchain_core.messages import BaseMessage, ToolMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough, RunnableLambda, RunnableConfig
from langchain_core.tracers import Run
from langchain_openai import ChatOpenAI
from langgraph.constants import END
from langgraph.graph import MessagesState, StateGraph

from internal.core.tools.builtin_tools.providers import BuiltinProviderManager
from internal.schema.app_schema import CompletionReq
from internal.service import (
    AppService,
    VectorDatabaseService,
    ApiToolService,
    EmbeddingsService,
)
from internal.service.conversation_service import ConversationService
from pkg.response import (
    success_json,
    validate_error_json,
    success_message,
    compact_generate_response,
)


@inject
@dataclass
class AppHandler:
    """应用控制器"""

    app_service: AppService
    api_tool_service: ApiToolService
    vector_database_service: VectorDatabaseService
    builtin_provider_manager: BuiltinProviderManager
    conversation_service: ConversationService

    def create_app(self):
        """调用服务创建新的APP记录"""
        app = self.app_service.create_app()
        return success_message(f"应用已经成功创建，id为{app.id}")

    def get_app(self, id: uuid.UUID):
        app = self.app_service.get_app(id)
        return success_message(f"应用已经成功获取，名字是{app.name}")

    def get_all_app(self):
        apps = self.app_service.get_all_app()
        return success_message(
            f"应用已经成功获取，列表是{[(str(app.id), app.name) for app in apps]}"
        )

    def update_app(self, id: uuid.UUID):
        app = self.app_service.update_app(id)
        return success_message(f"应用已经成功修改，修改的名字是:{app.name}")

    def delete_app(self, id: uuid.UUID):
        app = self.app_service.delete_app(id)
        return success_message(f"应用已经成功删除，id为:{app.id}")

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

    def debug(self, app_id: uuid.UUID):
        req = CompletionReq()

        if not req.validate():
            return validate_error_json(req.errors)

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "你是一个AI助手"),
                MessagesPlaceholder("history"),
                ("human", "{query}"),
            ]
        )

        memory = ConversationBufferWindowMemory(
            k=3,
            return_messages=True,
            output_key="output",
            input_key="query",
            chat_memory=FileChatMessageHistory("./storage/memory/chat_history.txt"),
        )

        llm = ChatOpenAI(
            model=os.getenv("OPENAI_MODEL"), api_key=os.getenv("OPENAI_API_KEY")
        )

        parser = StrOutputParser()

        retriever = (
            self.vector_database_service.get_retriever()
            | self.vector_database_service.combine_documents
        )

        chain = (
            RunnablePassthrough.assign(
                history=RunnableLambda(self._load_memory_variables)
                | itemgetter("history"),
                context=itemgetter("query") | retriever,
            )
            | prompt
            | llm
            | parser
        ).with_listeners(
            on_end=self._save_context,
        )

        chain_input = {"query": req.query.data}

        content = chain.invoke(
            chain_input,
            config={
                "configurable": {
                    "memory": memory,
                }
            },
        )

        return success_json({"content": content})

    def ping(self):
        human_message = "你可以简单介绍下Agent吗?LLM与Agent有什么关联"
        ai_message = "Agent（智能代理） 是一种能够 自主感知环境、做出决策并执行动作 的智能系统，通常基于大语言模型（LLM）或规则引擎驱动。它的核心目标是 替代或辅助人类完成特定任务，例如回答问题、自动化流程、数据分析等。"
        content = self.conversation_service.generate_suggested_questions(ai_message)

        return success_json({"content": content})
