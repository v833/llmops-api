import os
from dataclasses import dataclass
from openai import OpenAI
from internal.exception.exception import FailException
from internal.schema import CompletionReq
from internal.service import AppService
from pkg.response import success_message, validate_error_json
from injector import inject
import uuid

@inject
@dataclass
class AppHandler:
  """应用控制器"""
  
  app_service: AppService
  
  def create_app(self):
    """调用服务创建新的APP记录"""
    app = self.app_service.create_app()
    return success_message(f"应用已经成功创建，id为{app.id}")

  def get_app(self, id: uuid.UUID):
    app = self.app_service.get_app(id)
    return success_message(f"应用已经成功获取，名字是{app.name}")
  
  def get_all_app(self):
    apps = self.app_service.get_all_app()
    return success_message(f"应用已经成功获取，列表是{[(str(app.id), app.name) for app in apps]}")

  def update_app(self, id: uuid.UUID):
    app = self.app_service.update_app(id)
    return success_message(f"应用已经成功修改，修改的名字是:{app.name}")

  def delete_app(self, id: uuid.UUID):
    app = self.app_service.delete_app(id)
    return success_message(f"应用已经成功删除，id为:{app.id}")

  def ping(self):
    raise FailException("ping")
    # return success_message({"ping": "pong"})

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

    return success_message(content)

