from operator import itemgetter
import os

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain_openai import ChatOpenAI

def retrieval(query:str):
  return '我是wang'


llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL"))

parser = StrOutputParser()

prompt = ChatPromptTemplate.from_template("""请根据用户的问题回答，可以参考对应的上下文进行生成。

<context>
{context}
</context>

用户的提问是: {query}""")

chain = RunnableParallel(
    {
        "context": RunnablePassthrough.assign(context=itemgetter("query")) | retrieval,
        "query": RunnablePassthrough()
    }
  ) | prompt | llm | parser

content = chain.invoke(
  {
    "query": "你好，我是谁?", 
  })

print(content)