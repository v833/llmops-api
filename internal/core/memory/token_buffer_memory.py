from dataclasses import dataclass
from flask_sqlalchemy import SQLAlchemy
from injector import inject

from internal.entity.conversation_entity import MessageStatus
from internal.model.conversation import Conversation, Message
from langchain_core.language_models import BaseLanguageModel
from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    trim_messages,
    get_buffer_string,
)


@inject
@dataclass
class TokenBufferMemory:
    db: SQLAlchemy
    conversation: Conversation
    model_instance: BaseLanguageModel

    def get_history_prompt_messages(
        self, max_token_limit: int = 2000, message_limit: int = 10
    ):
        if self.conversation is None:
            return []

        messages = (
            self.db.session.query(Message)
            .filter(
                Message.conversation_id == self.conversation.id,
                Message.answer != "",
                Message.is_deleted == False,
                Message.status == MessageStatus.NORMAL,
            )
            .order_by(Message.created_at.desc())
            .limit(message_limit)
            .all()
        )

        messages = list(reversed(messages))

        prompt_messages = []
        for message in messages:
            prompt_messages.extend(
                [
                    HumanMessage(content=message.query),
                    AIMessage(content=message.answer),
                ]
            )

        return trim_messages(
            prompt_messages,
            max_token_limit=max_token_limit,
            token_counter=self.model_instance,
            strategy="last",
        )

    def get_history_prompt_text(
        self,
        human_prefix: str = "Human",
        ai_prefix: str = "AI",
        max_token_limit: int = 2000,
        message_limit: int = 10,
    ):
        """根据传递的数据获取指定会话历史消息提示文本(短期记忆的文本形式，用于文本生成模型)"""
        # 1.根据传递的信息获取历史消息列表
        messages = self.get_history_prompt_messages(max_token_limit, message_limit)

        # 2.调用LangChain集成的get_buffer_string()函数将消息列表转换成文本
        return get_buffer_string(messages, human_prefix, ai_prefix)
