from dataclasses import dataclass
from typing import Any
from uuid import UUID
from flask import Flask
from injector import inject
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
import os
from langchain_core.output_parsers import PydanticOutputParser
from internal.core.agent.entities.queue_entity import AgentThought, QueueEvent
from internal.entity.conversation_entity import (
    SUMMARIZER_TEMPLATE,
    CONVERSATION_NAME_TEMPLATE,
    ConversationInfo,
    SUGGESTED_QUESTIONS_TEMPLATE,
    InvokeFrom,
    SuggestedQuestions,
)
from internal.model.conversation import Conversation, Message, MessageAgentThought
from internal.service.base_service import BaseService
from pkg.sqlalchemy import SQLAlchemy
import logging
import json
from dotenv import load_dotenv

load_dotenv()


@inject
@dataclass
class ConversationService(BaseService):
    db: SQLAlchemy

    @classmethod
    def summary(cls, human_message: str, ai_message: str, old_summary: str = ""):
        prompt = ChatPromptTemplate.from_template(SUMMARIZER_TEMPLATE)

        llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL"), temperature=0.5)

        summary_chain = prompt | llm | StrOutputParser()

        new_summary = summary_chain.invoke(
            {
                "summary": old_summary,
                "new_lines": f"Human: {human_message}\nAI: {ai_message}",
            }
        )

        return new_summary

    @classmethod
    def generate_conversation_name(cls, query: str):
        """根据传递的query生成对应的会话名字，并且语言与用户的输入保持一致"""
        # 1.创建prompt
        parser = PydanticOutputParser(pydantic_object=ConversationInfo)

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    CONVERSATION_NAME_TEMPLATE + "\n{format_instructions}",
                ),
                ("human", "{query}"),
            ]
        ).partial(format_instructions=parser.get_format_instructions())

        # 2.构建大语言模型实例，并且将大语言模型的温度调低，降低幻觉的概率
        llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL"), temperature=0)

        # 3.构建链应用
        chain = prompt | llm | StrOutputParser()

        # 4.提取并整理query，截取长度过长的部分
        if len(query) > 2000:
            query = query[:300] + "...[TRUNCATED]..." + query[-300:]
        query = query.replace("\n", " ")

        # 5.调用链并获取会话信息
        response = chain.invoke({"query": query})

        response = response.replace("```json", "").replace("```", "").strip()
        conversation_info = json.loads(response)

        # 6.提取会话名称
        name = "新的会话"
        try:
            name = conversation_info.get("subject")
        except Exception as e:
            logging.exception(
                f"提取会话名称出错, conversation_info: {conversation_info}, 错误信息: {str(e)}"
            )
        if len(name) > 75:
            name = name[:75] + "..."

        return name

    @classmethod
    def generate_suggested_questions(cls, histories: str):
        """根据传递的历史信息生成最多不超过3个的建议问题"""
        # 1.创建prompt

        parser = PydanticOutputParser(pydantic_object=SuggestedQuestions)
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", SUGGESTED_QUESTIONS_TEMPLATE + "\n{format_instructions}"),
                ("human", "{histories}"),
            ]
        ).partial(format_instructions=parser.get_format_instructions())

        # 2.构建大语言模型实例，并且将大语言模型的温度调低，降低幻觉的概率
        llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL"), temperature=0)

        # 3.构建链应用
        chain = prompt | llm | StrOutputParser()

        # 4.调用链并获取建议问题列表
        response = chain.invoke({"histories": histories})

        response = response.replace("```json", "").replace("```", "").strip()
        suggested_questions = json.loads(response)
        # 5.提取建议问题列表
        questions = []
        try:
            questions = suggested_questions.get("questions")
        except Exception as e:
            logging.exception(
                f"生成建议问题出错, suggested_questions: {suggested_questions}, 错误信息: {str(e)}"
            )
        if len(questions) > 3:
            questions = questions[:3]

        return questions

    def save_agent_thoughts(
        self,
        flask_app: Flask,
        account_id: UUID,
        app_id: UUID,
        app_config: dict[str, Any],
        conversation_id: UUID,
        message_id: UUID,
        agent_thoughts: list[AgentThought],
    ):
        """存储智能体推理步骤消息"""
        with flask_app.app_context():
            # 1.定义变量存储推理位置及总耗时
            position = 0
            latency = 0

            # 2.在子线程中重新查询conversation以及message，确保对象会被子线程的会话管理到
            conversation = self.get(Conversation, conversation_id)
            message = self.get(Message, message_id)

            # 3.循环遍历所有的智能体推理过程执行存储操作
            for agent_thought in agent_thoughts:
                # 4.存储长期记忆召回、推理、消息、动作、知识库检索等步骤
                if agent_thought.event in [
                    QueueEvent.LONG_TERM_MEMORY_RECALL,
                    QueueEvent.AGENT_THOUGHT,
                    QueueEvent.AGENT_MESSAGE,
                    QueueEvent.AGENT_ACTION,
                    QueueEvent.DATASET_RETRIEVAL,
                ]:
                    # 5.更新位置及总耗时
                    position += 1
                    latency += agent_thought.latency

                    # 6.创建智能体消息推理步骤
                    self.create(
                        MessageAgentThought,
                        app_id=app_id,
                        conversation_id=conversation.id,
                        message_id=message.id,
                        invoke_from=InvokeFrom.DEBUGGER,
                        created_by=account_id,
                        position=position,
                        event=agent_thought.event,
                        thought=agent_thought.thought,
                        observation=agent_thought.observation,
                        tool=agent_thought.tool,
                        tool_input=agent_thought.tool_input,
                        message=agent_thought.message,
                        answer=agent_thought.answer,
                        latency=agent_thought.latency,
                    )

                # 7.检测事件是否为Agent_message
                if agent_thought.event == QueueEvent.AGENT_MESSAGE:
                    # 8.更新消息信息
                    self.update(
                        message,
                        message=agent_thought.message,
                        answer=agent_thought.answer,
                        latency=latency,
                    )

                    # 9.检测是否开启长期记忆
                    if app_config["long_term_memory"]["enable"]:
                        new_summary = self.summary(
                            message.query, agent_thought.answer, conversation.summary
                        )
                        self.update(
                            conversation,
                            summary=new_summary,
                        )

                    # 10.处理生成新会话名称
                    if conversation.is_new:
                        new_conversation_name = self.generate_conversation_name(
                            message.query
                        )
                        self.update(
                            conversation,
                            name=new_conversation_name,
                        )

                # 11.判断是否为停止或者错误，如果是则需要更新消息状态
                if agent_thought.event in [
                    QueueEvent.TIMEOUT,
                    QueueEvent.STOP,
                    QueueEvent.ERROR,
                ]:
                    self.update(
                        message,
                        status=agent_thought.event,
                        error=agent_thought.observation,
                    )
                    break
