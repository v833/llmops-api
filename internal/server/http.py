from flask import Flask, Response
from internal.router import Router
from config import Config
from internal.exception import CustomException
from pkg.response import json,Response,HttpCode
import os

class Http(Flask):
  def __init__(self, *args,config:Config, router:Router, **kwargs):
    super().__init__(*args, **kwargs)
    
    if config:
      self.config.from_object(config)
    
    self.register_error_handler(Exception, self._register_error_handler)
    
    router.register_router(self)
  
  def _register_error_handler(self, err: Exception):
    if isinstance(err, CustomException):
      return json(Response(code=err.code, message=err.message, data=err.data if err.data is not None else {}))
    
    if self.debug or os.getenv("FLASK_DEBUG"):
      raise err
    else:
      return json(Response(code=HttpCode.FAIL, message=str(err), data={}))
