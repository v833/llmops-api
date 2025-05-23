from internal.extension.module_extension import injector
from internal.server import Http
from internal.router import Router
from config import Config
from pkg.sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from internal.middleware import Middleware
from flask_weaviate import FlaskWeaviate
import dotenv
import os

if os.environ.get("FLASK_DEBUG") == "0" or os.environ.get("FLASK_ENV") == "production":
    from gevent import monkey

    monkey.patch_all()
    import grpc.experimental.gevent

    grpc.experimental.gevent.init_gevent()

dotenv.load_dotenv()
app = Http(
    __name__,
    config=Config(),
    db=injector.get(SQLAlchemy),
    migrate=injector.get(Migrate),
    weaviate=injector.get(FlaskWeaviate),
    router=injector.get(Router),
    login_manager=injector.get(LoginManager),
    middleware=injector.get(Middleware),
)

celery = app.extensions["celery"]

if __name__ == "__main__":
    app.run(debug=True, port=5000)
