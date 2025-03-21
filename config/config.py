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
