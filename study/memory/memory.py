import os
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from operator import itemgetter

prompt = ChatPromptTemplate.from_messages([
    ('system', '你是一个AI助手'),
    MessagesPlaceholder('history'),
    ('human', '{query}')
])

memory = ConversationBufferWindowMemory(
  k=2,
  return_messages=True,
  output_key='output',
  input_key='query'
  )

llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL"), api_key=os.getenv("OPENAI_API_KEY"))

chain = RunnablePassthrough.assign(
  history=RunnableLambda(memory.load_memory_variables) | itemgetter('history')
) | prompt | llm | StrOutputParser()

while True:
  query = input("Human: ")
  if (query == 'q'):
    break

  chain_input = {'query': query}
  
  res = chain.stream(chain_input)
  
  print('AI: ', end='', flush=True)
  output = ''
  for chunk in res:
    output += chunk
    print(chunk, end='', flush=True)
  memory.save_context(chain_input, {'output': output})
  print()
