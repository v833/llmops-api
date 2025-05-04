from flask import Flask
import redis
from redis.connection import Connection, SSLConnection

redis_client = redis.Redis()


def redis_init_app(app: Flask):
    connection_class = Connection
    if app.config.get("REDIS_USE_SSL", False):
        connection_class = SSLConnection

    redis_client.connection_pool = redis.ConnectionPool(
        **{
            "host": app.config["REDIS_HOST"],
            "port": app.config["REDIS_PORT"],
            "username": app.config["REDIS_USERNAME"],
            "password": app.config["REDIS_PASSWORD"],
            "db": app.config["REDIS_DB"],
            "encoding": "utf-8",
            "encoding_errors": "strict",
            "decode_responses": False,
        },
        connection_class=connection_class
    )

    app.extensions["redis"] = redis_client
