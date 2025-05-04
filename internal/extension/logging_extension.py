import logging
import os.path
from logging.handlers import TimedRotatingFileHandler

from flask import Flask


def logging_init_app(app: Flask):
    """日志记录器初始化"""
    # 1.设置日志存储的文件夹，如果不存在则创建
    log_folder = os.path.join(os.getcwd(), "storage", "log")
    if not os.path.exists(log_folder):
        os.makedirs(log_folder)

    # 2.定义日志的文件名
    log_file = os.path.join(log_folder, "app.log")

    # 3.设置日志的格式，并且让日志每天更新一次
    handler = TimedRotatingFileHandler(
        log_file,
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8",
    )
    formatter = logging.Formatter(
        "[%(asctime)s.%(msecs)03d] %(filename)s -> %(funcName)s line:%(lineno)d [%(levelname)s]: %(message)s"
    )
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(formatter)
    logging.getLogger().addHandler(handler)

    # 4.在开发环境下同时将日志输出到控制台
    if app.debug or os.getenv("FLASK_ENV") == "development":
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logging.getLogger().addHandler(console_handler)
