
from langchain_community.chat_message_histories import FileChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.runnables import RunnableWithMessageHistory
from operator import itemgetter
import os

llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL"), api_key=os.getenv("OPENAI_API_KEY"))

prompt = ChatPromptTemplate.from_messages(
  [
    ('system', '你是一个AI助手'),
    MessagesPlaceholder('history'),
    ('human', '{query}')
  ]
)

chain = prompt | llm | StrOutputParser()

store = {}

def get_session_history(session_id):
  if session_id not in store:
    store[session_id] = FileChatMessageHistory(f'./chat_history_{session_id}.txt')
  
  return store[session_id]

with_message_chain = RunnableWithMessageHistory(
  chain,
  get_session_history,
  input_messages_key="query",
  history_messages_key="history",
)

while True:
  query = input("请输入: ")

  if query == "q":
    exit(0)
  
  res = with_message_chain.stream(
    {"query": query},
    config={"configurable": {"session_id": '2025'}}
  )
  
  print('AI', flush=True, end='')
  for chunk in res:
    print(chunk, flush=True, end='')

  print()