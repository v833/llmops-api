from flask import Flask, Blueprint
from internal.handler import AppHandler
from injector import inject
from dataclasses import dataclass

@inject
@dataclass
class Router:
  """路由"""
  app_handler: AppHandler
  
  def register_router(self, app: Flask):
    """注册路由"""
    # 创建蓝图
    bp = Blueprint('llmops', __name__, url_prefix="")
    
    # 将url与对应的控制器方法绑定
    bp.add_url_rule('/ping', view_func=self.app_handler.ping)
    
    # 注册蓝图
    app.register_blueprint(bp)