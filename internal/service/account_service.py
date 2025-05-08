import base64
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from flask import request
from injector import inject

from internal.exception import FailException
from internal.model import Account, AccountOAuth
from pkg.password import hash_password, compare_password
from pkg.sqlalchemy import SQLAlchemy
from .base_service import BaseService
from .jwt_service import JwtService


@inject
@dataclass
class AccountService(BaseService):
    """账号服务"""

    db: SQLAlchemy
    jwt_service: JwtService

    def get_account(self, account_id: UUID) -> Account:
        """根据id获取指定的账号模型"""
        return self.get(Account, account_id)

    def get_account_oauth_by_provider_name_and_openid(
        self,
        provider_name: str,
        openid: str,
    ) -> AccountOAuth:
        """根据传递的提供者名字+openid获取第三方授权认证记录"""
        return (
            self.db.session.query(AccountOAuth)
            .filter(
                AccountOAuth.provider == provider_name,
                AccountOAuth.openid == openid,
            )
            .one_or_none()
        )

    def get_account_by_email(self, email: str) -> Account:
        """根据传递的邮箱查询账号信息"""
        return (
            self.db.session.query(Account)
            .filter(
                Account.email == email,
            )
            .one_or_none()
        )

    def create_account(self, **kwargs) -> Account:
        """根据传递的键值对创建账号信息"""
        return self.create(Account, **kwargs)

    def update_password(self, password: str, account: Account) -> Account:
        """更新当前账号密码信息"""
        # 1.生成密码随机盐值
        salt = secrets.token_bytes(16)
        base64_salt = base64.b64encode(salt).decode()

        # 2.利用盐值和password进行加密
        password_hashed = hash_password(password, salt)
        base64_password_hashed = base64.b64encode(password_hashed).decode()

        # 3.更新账号信息
        self.update_account(
            account, password=base64_password_hashed, password_salt=base64_salt
        )

        return account

    def update_account(self, account: Account, **kwargs) -> Account:
        """根据传递的信息更新账号"""
        self.update(account, **kwargs)
        return account

    def password_login(self, email: str, password: str) -> dict[str, Any]:
        """根据传递的密码+邮箱登录特定的账号"""
        # 1.根据传递的邮箱查询账号是否存在
        account = self.get_account_by_email(email)
        if not account:
            raise FailException("账号不存在或者密码错误，请核实后重试")

        # 2.校验账号密码是否正确
        if not account.is_password_set or not compare_password(
            password,
            account.password,
            account.password_salt,
        ):
            raise FailException("账号不存在或者密码错误，请核实后重试")

        # 3.生成凭证信息
        expire_at = int((datetime.now() + timedelta(days=30)).timestamp())
        payload = {
            "sub": str(account.id),
            "iss": "llmops",
            "exp": expire_at,
        }
        access_token = self.jwt_service.generate_token(payload)

        # 4.更新账号的登录信息
        self.update(
            account,
            last_login_at=datetime.now(),
            last_login_ip=request.remote_addr,
        )

        return {
            "expire_at": expire_at,
            "access_token": access_token,
        }
