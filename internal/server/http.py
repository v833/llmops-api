from flask import Flask
from internal.router import Router
from config import Config

class Http(Flask):
  def __init__(self, *args,config:Config, router:Router, **kwargs):
    super().__init__(*args, **kwargs)
    
    if config:
      self.config.from_object(config)
    
    router.register_router(self)