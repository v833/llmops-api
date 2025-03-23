from langchain_core.messages import AIMessage
from langchain_core.prompts import HumanMessagePromptTemplate, PromptTemplate, ChatPromptTemplate,MessagesPlaceholder

prompt = PromptTemplate.from_template("请讲一个关于{subject}的冷笑话")

prompt_value = prompt.invoke({'subject': '程序员'})

# print(prompt.format(subject="程序员"))
# print(prompt_value.to_string())
# print(prompt_value.to_messages())

chat_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant."),
    MessagesPlaceholder('chat_history'),
    HumanMessagePromptTemplate.from_template("What is 2+2?")
]).partial(chat_history=[])

chat_prompt_value = chat_prompt.invoke({'chat_history': [
  ('human', 'What is 2+2?'),
  ('assistant', '2+2=4'),
  
]})

print(chat_prompt_value.to_string())