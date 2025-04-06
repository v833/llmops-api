from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
import os
from langchain_core.runnables import ConfigurableField

prompt = PromptTemplate.from_template("{query}")

llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL"), api_key=os.getenv("OPENAI_API_KEY")).configurable_alternatives(
  ConfigurableField(id="llm"),
  default_key=os.getenv("OPENAI_MODEL"),
  gpt4_key=ChatOpenAI(mode="gpt-4", api_key=os.getenv("OPENAI_API_KEY"))
)

chain = prompt | llm | StrOutputParser()

content = chain.invoke({"query": "你是谁？"}, config={
  "configurable": {
    "llm": "gpt-4",
    }
  }
)