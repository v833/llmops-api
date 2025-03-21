from injector import Module, Binder
from pkg.sqlalchemy import SQLAlchemy
from internal.extension.database_extension import db

class ExtensionModule(Module):
    """扩展模块的依赖注入"""

    def configure(self, binder: Binder) -> None:
        binder.bind(SQLAlchemy, to=db)
