from internal.server import Http
from internal.router import Router
from injector import Injector
from config import Config

injector = Injector()

app = Http(__name__,config=Config(), router=injector.get(Router))

if __name__ == '__main__':
  app.run(debug=True, port=5000)