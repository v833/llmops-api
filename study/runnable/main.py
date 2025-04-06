
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import os
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_community.chat_message_histories import FileChatMessageHistory

llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL"), api_key=os.getenv("OPENAI_API_KEY"))

prompt = ChatPromptTemplate.from_messages(
    [
        ('system', '你是一个AI助手'),
        ('human', '{query}')
    ]
)

chain = prompt | llm.bind(stop="DeepSeek") | StrOutputParser()


content = chain.invoke({"query": "你是谁？"})

print(content)