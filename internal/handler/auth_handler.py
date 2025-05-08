from dataclasses import dataclass

from flask_login import logout_user, login_required
from injector import inject

from internal.schema.auth_schema import PasswordLoginReq, PasswordLoginResp
from internal.service import AccountService
from pkg.response import success_message, validate_error_json, success_json


@inject
@dataclass
class AuthHandler:
    """LLMOps平台自有授权认证处理器"""

    account_service: AccountService

    def password_login(self):
        """账号密码登录"""
        # 1.提取请求并校验数据
        req = PasswordLoginReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 2.调用服务登录账号
        credential = self.account_service.password_login(
            req.email.data, req.password.data
        )

        # 3.创建响应结构并返回
        resp = PasswordLoginResp()

        return success_json(resp.dump(credential))

    @login_required
    def logout(self):
        """退出登录，用于提示前端清除授权凭证"""
        logout_user()
        return success_message("退出登陆成功")
