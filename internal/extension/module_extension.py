from injector import Module, Binder, Injector
from internal.extension.redis_extension import redis_client
from pkg.sqlalchemy import SQLAlchemy
from internal.extension import db, migrate
from flask_migrate import Migrate
from redis import Redis


class ExtensionModule(Module):
    """扩展模块的依赖注入"""

    def configure(self, binder: Binder):
        binder.bind(SQLAlchemy, to=db)
        binder.bind(Migrate, to=migrate)
        binder.bind(Redis, to=redis_client)


injector = Injector([ExtensionModule])
