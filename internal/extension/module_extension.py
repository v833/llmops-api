from injector import Module, Binder, Injector
from internal.extension.redis_extension import redis_client
from pkg.sqlalchemy import SQLAlchemy
from internal.extension import db, migrate
from flask_migrate import Migrate
from redis import Redis
from flask_login import LoginManager
from internal.extension.login_extension import login_manager
from flask_weaviate import FlaskWeaviate
from internal.extension.weaviate_extension import weaviate


class ExtensionModule(Module):
    """扩展模块的依赖注入"""

    def configure(self, binder: Binder):
        binder.bind(SQLAlchemy, to=db)
        binder.bind(Migrate, to=migrate)
        binder.bind(Redis, to=redis_client)
        binder.bind(LoginManager, to=login_manager)
        binder.bind(
            FlaskWeaviate,
            to=weaviate,
        )


injector = Injector([ExtensionModule])
