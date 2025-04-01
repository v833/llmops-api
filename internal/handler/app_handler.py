import os
from dataclasses import dataclass
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.chat_message_histories import FileChatMessageHistory
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_openai import ChatOpenAI
from internal.exception.exception import FailException
from internal.schema import CompletionReq
from internal.service import AppService
from pkg.response import success_message, validate_error_json, success_json
from injector import inject
from operator import itemgetter
from langchain.memory import ConversationBufferWindowMemory
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

  def debug(self, app_id: uuid.UUID):
    req = CompletionReq()
    
    if not req.validate():
      return validate_error_json(req.errors)
    
    prompt = ChatPromptTemplate.from_messages(
      [
        ('system', '你是一个AI助手'),
        MessagesPlaceholder('history'),
        ('human', '{query}')
      ]
    )
    
    memory = ConversationBufferWindowMemory(
      k=3,
      return_messages=True,
      output_key='output',
      input_key='query',
      chat_memory=FileChatMessageHistory('./storage/memory/chat_history.txt'),
    )
    
    llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL"), api_key=os.getenv("OPENAI_API_KEY"))
    
    parser = StrOutputParser()
    
    chain = RunnablePassthrough.assign(
        history=RunnableLambda(memory.load_memory_variables) | itemgetter('history')
      ) | prompt | llm | parser
    
    chain_input = {'query': req.query.data}
    
    content = chain.invoke(chain_input)
    
    memory.save_context(chain_input, {"output": content})

    return success_json({"content": content})

