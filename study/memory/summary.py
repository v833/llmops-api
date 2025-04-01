from openai import OpenAI
from dataclasses import dataclass
import os

base_url = os.getenv("OPENAI_API_BASE")
api_key = os.getenv("OPENAI_API_KEY")


class ConversationSummaryBufferMemory:
  
  def __init__(self, summary:str = '', chat_histories:list = None, max_tokens:int = 300):
    self.summary = summary
    self.chat_histories = chat_histories or []
    self.max_tokens = max_tokens
    self._client = OpenAI(base_url=base_url, api_key=api_key)
  
  @classmethod
  def get_num_tokens(cls, query:str):
    return len(query)
  
  def save_context(self, human_query:str, ai_content:str):
    self.chat_histories.append({'human': human_query, 'ai': ai_content})
    
    buffer_string = self.get_buffer_string()
    num_tokens = self.get_num_tokens(buffer_string)
    
    if num_tokens > self.max_tokens:
      first_chat = self.chat_histories.pop(0)
      self.summary = self.summary_text(self.summary, f"{first_chat['human']}: {first_chat['ai']}")
    
  def get_buffer_string(self):
    buffer_string = ""
    for chat_history in self.chat_histories:
      buffer_string += f"{chat_history['human']}: {chat_history['ai']}\n"
    return buffer_string
  
  def load_memory_variables(self):
    return {
      'history': f'摘要: {self.summary}\n\n历史消息: {self.get_buffer_string()}'
    }
    
  def summary_text(self, origin_summary:str, new_line:str):
    response = self._client.chat.completions.create(
      model="deepseek-chat",
      messages=[
        {"role": "user", "content": f"请根据下面的对话，生成一个简短的摘要。\n\n{origin_summary}\n\n{new_line}\n\n"}
      ]
    )
    return response.choices[0].message.content
    
client = OpenAI(base_url=base_url, api_key=api_key)
memory = ConversationSummaryBufferMemory(summary='', chat_histories=[], max_tokens=300)

while True:
  query = input("Human: ")
  
  if (query == 'q'):
    break
  
  memory_variables = memory.load_memory_variables()

  answer_prompt = (
    "你是一个强大的人工智能助手，你的任务是回答用户的问题。\n\n"
    f"{memory_variables.get('history')}\n\n"
    f"用户的提问是: {query}\n\n"
  )

  response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
      {"role": "user", "content": answer_prompt}
    ],
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
  memory.save_context(query, ai_content)