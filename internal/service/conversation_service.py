from dataclasses import dataclass
from injector import inject
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
import os
from langchain_core.output_parsers import PydanticOutputParser
from internal.entity.conversation_entity import (
    SUMMARIZER_TEMPLATE,
    CONVERSATION_NAME_TEMPLATE,
    ConversationInfo,
    SUGGESTED_QUESTIONS_TEMPLATE,
    SuggestedQuestions,
)
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
