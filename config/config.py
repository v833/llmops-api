import os


def _get_bool_env(key: str) -> bool:
    return os.getenv(key) in ["True", "true", "1"]


class Config:
    def __init__(self):
        # 配置wtf
        self.WTF_CSRF_ENABLED = _get_bool_env("WTF_CSRF_ENABLED")

        # 配置数据库配置
        self.SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI")
        self.SQLALCHEMY_ENGINE_OPTIONS = {
            "pool_size": int(os.getenv("SQLALCHEMY_POOL_SIZE")),
            "pool_recycle": int(os.getenv("SQLALCHEMY_POOL_RECYCLE")),
        }
        self.SQLALCHEMY_ECHO = _get_bool_env("SQLALCHEMY_ECHO")

        self.REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
        self.REDIS_PORT = os.getenv("REDIS_PORT", 6379)
        self.REDIS_USERNAME = os.getenv("REDIS_USERNAME")
        self.REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
        self.REDIS_DB = os.getenv("REDIS_DB", 0)
        self.REDIS_USE_SSL = _get_bool_env("REDIS_USE_SSL")

        self.CELERY = {
            "broker_url": f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{os.getenv('CELERY_BROKER_DB')}",
            "result_backend": f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{os.getenv('CELERY_RESULT_BACKEND_DB')}",
            "task_ignore_result": _get_bool_env("CELERY_TASK_IGNORE_RESULT"),
            "result_expires": os.getenv("CELERY_RESULT_EXPIRES"),
            "broker_connection_retry_on_startup": os.getenv(
                "CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP"
            ),
        }
        # Weaviate向量数据库配置
        self.WEAVIATE_HTTP_HOST = os.getenv("WEAVIATE_HTTP_HOST")
        self.WEAVIATE_HTTP_PORT = os.getenv("WEAVIATE_HTTP_PORT")
        self.WEAVIATE_GRPC_HOST = os.getenv("WEAVIATE_GRPC_HOST")
        self.WEAVIATE_GRPC_PORT = os.getenv("WEAVIATE_GRPC_PORT")
        self.WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY")

        self.ASSISTANT_AGENT_ID = os.getenv("ASSISTANT_AGENT_ID")
