from langchain_core.callbacks import BaseCallbackHandler, StdOutCallbackHandler
from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
import os


llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL"), api_key=os.getenv("OPENAI_API_KEY"))

prompt = ChatPromptTemplate.from_template("{query}")

chain = prompt | llm | StrOutputParser()

content = chain.invoke({"query": "请讲一个程序员的冷笑话"}, config={"callbacks": [StdOutCallbackHandler()]})

print(content)
