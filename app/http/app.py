from internal.extension.module_extension import injector
from internal.server import Http
from internal.router import Router
from injector import Injector
from config import Config
from pkg.sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Http(
    __name__,
    config=Config(),
    db=injector.get(SQLAlchemy),
    migrate=injector.get(Migrate),
    router=injector.get(Router),
)

celery = app.extensions["celery"]

if __name__ == "__main__":
    app.run(debug=True, port=5000)
