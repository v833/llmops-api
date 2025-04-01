from langchain_community.chat_message_histories import FileChatMessageHistory
from openai import OpenAI
import os

base_url = os.getenv("OPENAI_API_BASE")
api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(base_url=base_url, api_key=api_key)

chat_history = FileChatMessageHistory('./memory.txt')

while True:
  query = input("Human: ")
  if (query == 'q'):
    break
  chat_history.add_user_message(query)
  
  system_prompt = (
        "你是OpenAI开发的ChatGPT聊天机器人，可以根据相应的上下文回复用户信息，上下文里存放的是人类与你对话的信息列表。\n\n"
        f"<context>{chat_history}</context>\n\n"
    )

  response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": query}
      ],  # 使用转换后的消息列表
    stream=True
  )
  print('AI: ', flush=True, end='')
  ai_content = ''
  for chunk in response:
    content = chunk.choices[0].delta.content
    if content is not None:
      ai_content += content
      print(content, end='', flush=True)
  print()
  chat_history.add_ai_message(ai_content)