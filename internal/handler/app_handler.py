import os
from openai import OpenAI
from internal.schema import CompletionReq
from pkg.response import success_json, validate_error_json

class AppHandler:
  """应用控制器"""
  def ping(self):
    return success_json({"ping": "pong"})

  def completion(self):
    req = CompletionReq()
    
    if not req.validate():
      return validate_error_json(req.errors)
    
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), 
                    base_url=os.getenv("OPENAI_API_BASE"))

    completion = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL"),
        messages=[
        {"role": "system", "content": "你是deepseek开发的聊天机器人, 请根据用户的问题给出准确的答案"},
        {"role": "user", "content": req.query.data},
    ],
    stream=False
    )
    
    content = completion.choices[0].message.content

    return success_json(content)

