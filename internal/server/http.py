import logging
from flask import Flask, Response
from internal.extension.celery_extension import celery_init_app
from internal.extension.redis_extension import redis_init_app
from internal.router import Router
from config import Config
from internal.exception import CustomException
from internal.extension import logging_init_app
from pkg.response import json, Response, HttpCode
import os
from pkg.sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS


class Http(Flask):
    def __init__(
        self,
        *args,
        config: Config,
        db: SQLAlchemy,
        migrate: Migrate,
        router: Router,
        **kwargs
    ):
        super().__init__(*args, **kwargs)

        if config:
            self.config.from_object(config)

        self.register_error_handler(Exception, self._register_error_handler)

        db.init_app(self)

        # with self.app_context():
        # db.drop_all()
        #   db.create_all()

        migrate.init_app(self, db, directory="internal/migration")
        logging_init_app(self)
        redis_init_app(self)
        celery_init_app(self)

        CORS(
            self,
            resources={
                r"/*": {
                    "origins": "*",
                    "supports_credentials": True,
                }
            },
        )

        router.register_router(self)

    def _register_error_handler(self, err: Exception):
        logging.error("An error occurred: %s", err, exc_info=True)

        if isinstance(err, CustomException):
            return json(
                Response(
                    code=err.code,
                    message=err.message,
                    data=err.data if err.data is not None else {},
                )
            )

        if self.debug or os.getenv("FLASK_DEBUG"):
            raise err
        else:
            return json(Response(code=HttpCode.FAIL, message=str(err), data={}))
