from internal.server import Http
from internal.router import Router
from injector import Injector
from config import Config
from pkg.sqlalchemy import SQLAlchemy
from module import ExtensionModule


injector = Injector([ExtensionModule])

app = Http(__name__,config=Config(), db=injector.get(SQLAlchemy), router=injector.get(Router))

if __name__ == '__main__':
  app.run(debug=True, port=5000)
  
  