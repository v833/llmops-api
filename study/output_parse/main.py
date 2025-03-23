

from langchain_openai import ChatOpenAI
import os 
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from pydantic import BaseModel, Field

class Joke(BaseModel):
  joke: str = Field(description="讲一个冷笑话")
  punchline: str = Field(description="冷笑话的笑点")


llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL"))

parser = JsonOutputParser(pydantic_object=Joke)

# print(parser.get_format_instructions())


prompt = ChatPromptTemplate.from_template("请根据用户的提问进行回答。\n{format_instructions}\n{query}").partial(
    format_instructions=parser.get_format_instructions())

joke = parser.invoke(llm.invoke(prompt.invoke({"query": "请讲一个关于程序员的冷笑话"})))

print(type(joke))
print(joke.get("punchline"))
print(joke)
