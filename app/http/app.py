import sys
import os

# 添加项目根目录到 Python 路径
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from internal.server import Http
from internal.router import Router
from injector import Injector

injector = Injector()

app = Http(__name__, router=injector.get(Router))

if __name__ == '__main__':
  app.run(debug=True, port=5000)