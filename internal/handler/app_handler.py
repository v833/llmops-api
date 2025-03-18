import os
from flask import request
from openai import OpenAI

class AppHandler:
  """应用控制器"""
  def ping(self):
    return {"ping": "pong"}

  def completion(self):
    query = request.json.get("query")
    
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), 
                    base_url=os.getenv("OPENAI_API_BASE"))

    completion = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL"),
        messages=[
        {"role": "system", "content": "你是deepseek开发的聊天机器人, 请根据用户的问题给出准确的答案"},
        {"role": "user", "content": query},
    ],
    stream=False
    )
    
    content = completion.choices[0].message.content

    return content

