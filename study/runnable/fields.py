from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
import os
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import ConfigurableField


prompt = PromptTemplate.from_template("请生成一个小于{x}的随机整数")

llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL"), api_key=os.getenv("OPENAI_API_KEY")).configurable_fields(
  temperature=ConfigurableField(
    id="llm_temperature",
    name="温度",
    description="控制生成文本的随机性，值越高，生成的文本越随机",
  ),
)
chain = prompt | llm | StrOutputParser()
content1 = chain.invoke({"x": 1000})

content2 = chain.invoke({'x': 1000}, config={
  "configurable": {
    "llm_temperature": 0
  }
})

content3 = chain.with_config(
  {
    "configurable": {
      "llm_temperature": 0
    }
  }
).invoke({"x": 1000})
