from datetime import datetime
import os

import dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

# dotenv.load_dotenv()

# 1.编排prompt
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是OpenAI开发的聊天机器人，请回答用户的问题，现在的时间是{now}"),
    ("human", "{query}"),
]).partial(now=datetime.now())

# 2.创建大语言模型
llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL"))

ai_message = llm.stream(prompt.invoke({"query": "现在是几点，请讲一个程序员的冷笑话"}))

for chunk in ai_message:
  print(chunk.content, flush=True, end='')