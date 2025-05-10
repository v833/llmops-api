import uuid
from dataclasses import dataclass
from typing import List
from datetime import datetime
from injector import inject

from internal.exception.exception import ForbiddenException, NotFoundException
from internal.model import App
from internal.service.base_service import BaseService
from pkg.sqlalchemy import SQLAlchemy
from internal.schema.app_schema import CreateAppReq
from internal.model import Account, AppConfigVersion

from internal.entity.app_entity import AppStatus, AppConfigType, DEFAULT_APP_CONFIG


@inject
@dataclass
class AppService(BaseService):
    """应用服务逻辑"""

    db: SQLAlchemy

    def create_app(self, req: CreateAppReq, account: Account) -> App:
        with self.db.auto_commit():
            # 1.创建模型的实体类
            app = App(
                id=uuid.uuid4(),
                account_id=account.id,
                name=req.name.data,
                icon=req.icon.data,
                description=req.description.data,
                status=AppStatus.DRAFT,
                updated_at=datetime.utcnow(),
                created_at=datetime.utcnow(),
            )
            # 2.将实体类添加到session会话中
            self.db.session.add(app)
            self.db.session.flush()

            # 3.添加草稿记录
            app_config_version = AppConfigVersion(
                id=uuid.uuid4(),
                app_id=app.id,
                version=0,
                config_type=AppConfigType.DRAFT,
                updated_at=datetime.utcnow(),
                created_at=datetime.utcnow(),
                **DEFAULT_APP_CONFIG,
            )
            self.db.session.add(app_config_version)
            self.db.session.flush()

            # 4.为应用添加草稿配置id
            app.draft_app_config_id = app_config_version.id

        # 5.返回创建的应用记录
        return app

    def get_app(self, app_id: uuid.UUID, account: Account) -> App:
        """根据传递的id获取应用的基础信息"""
        # 1.查询数据库获取应用基础信息
        app = self.get(App, app_id)

        # 2.判断应用是否存在
        if not app:
            raise NotFoundException("该应用不存在，请核实后重试")

        # 3.判断当前账号是否有权限访问该应用
        if app.account_id != account.id:
            raise ForbiddenException("当前账号无权限访问该应用，请核实后尝试")

        return app
