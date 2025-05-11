from sqlalchemy import (
    Column,
    UUID,
    String,
    Text,
    Integer,
    DateTime,
    PrimaryKeyConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB

from internal.entity.app_entity import AppConfigType, DEFAULT_APP_CONFIG
from internal.entity.conversation_entity import InvokeFrom
from internal.extension.database_extension import db
from .conversation import Conversation


class App(db.Model):
    """AI应用基础模型类"""

    __tablename__ = "app"
    __table_args__ = (PrimaryKeyConstraint("id", name="pk_app_id"),)
    id = Column(UUID, nullable=False, server_default=text("uuid_generate_v4()"))
    account_id = Column(UUID, nullable=False)  # 创建账号id
    app_config_id = Column(UUID, nullable=True)  # 发布配置id，当值为空时代表没有发布
    draft_app_config_id = Column(UUID, nullable=True)  # 关联的草稿配置id
    debug_conversation_id = Column(
        UUID, nullable=True
    )  # 应用调试会话id，为None则代表没有会话信息
    name = Column(
        String(255), nullable=False, server_default=text("''::character varying")
    )  # 应用名字
    icon = Column(
        String(255), nullable=False, server_default=text("''::character varying")
    )  # 应用图标
    description = Column(
        Text, nullable=False, server_default=text("''::text")
    )  # 应用描述
    status = Column(
        String(255), nullable=False, server_default=text("''::character varying")
    )  # 应用状态
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(0)"),
        server_onupdate=text("CURRENT_TIMESTAMP(0)"),
    )
    created_at = Column(
        DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP(0)")
    )

    @property
    def app_config(self) -> "AppConfig":
        """只读属性，返回当前应用的运行配置"""
        if not self.app_config_id:
            return None
        return db.session.query(AppConfig).get(self.app_config_id)

    @property
    def draft_app_config(self) -> "AppConfigVersion":
        """只读属性，返回当前应用的草稿配置"""
        # 1.获取当前应用的草稿配置
        app_config_version = (
            db.session.query(AppConfigVersion)
            .filter(
                AppConfigVersion.app_id == self.id,
                AppConfigVersion.config_type == AppConfigType.DRAFT,
            )
            .one_or_none()
        )

        # 2.检测配置是否存在，如果不存在则创建一个默认值
        if not app_config_version:
            app_config_version = AppConfigVersion(
                app_id=self.id,
                version=0,
                config_type=AppConfigType.DRAFT,
                **DEFAULT_APP_CONFIG
            )
            db.session.add(app_config_version)
            db.session.commit()

        return app_config_version

    @property
    def debug_conversation(self) -> "Conversation":
        """获取应用的调试会话记录"""
        # 1.根据debug_conversation_id获取调试会话记录
        debug_conversation = None
        if self.debug_conversation_id is not None:
            debug_conversation = (
                db.session.query(Conversation)
                .filter(
                    Conversation.id == self.debug_conversation_id,
                    Conversation.invoke_from == InvokeFrom.DEBUGGER,
                )
                .one_or_none()
            )

        # 2.检测数据是否存在，如果不存在则创建
        if not self.debug_conversation_id or not debug_conversation:
            # 3.开启数据库自动提交上下文
            with db.auto_commit():
                # 4.创建应用调试会话记录并刷新获取会话id
                debug_conversation = Conversation(
                    app_id=self.id,
                    name="New Conversation",
                    invoke_from=InvokeFrom.DEBUGGER,
                    created_by=self.account_id,
                )
                db.session.add(debug_conversation)
                db.session.flush()

                # 5.更新当前记录的debug_conversation_id
                self.debug_conversation_id = debug_conversation.id

        return debug_conversation


class AppConfig(db.Model):
    """应用配置模型"""

    __tablename__ = "app_config"
    __table_args__ = (PrimaryKeyConstraint("id", name="pk_app_config_id"),)

    id = Column(
        UUID, nullable=False, server_default=text("uuid_generate_v4()")
    )  # 配置id
    app_id = Column(UUID, nullable=False)  # 关联应用id
    model_config = Column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )  # 模型配置
    dialog_round = Column(
        Integer, nullable=False, server_default=text("0")
    )  # 鞋带上下文轮数
    preset_prompt = Column(
        Text, nullable=False, server_default=text("''::text")
    )  # 预设prompt
    tools = Column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )  # 应用关联工具列表
    workflows = Column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )  # 应用关联的工作流列表
    retrieval_config = Column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )  # 检索配置
    long_term_memory = Column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )  # 长期记忆配置
    opening_statement = Column(
        Text, nullable=False, server_default=text("''::text")
    )  # 开场白文案
    opening_questions = Column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )  # 开场白建议问题列表
    speech_to_text = Column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )  # 语音转文本配置
    text_to_speech = Column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )  # 文本转语音配置
    suggested_after_answer = Column(
        JSONB,
        nullable=False,
        server_default=text("'{\"enable\": true}'::jsonb"),
    )  # 回答后生成建议问题
    review_config = Column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )  # 审核配置
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(0)"),
        server_onupdate=text("CURRENT_TIMESTAMP(0)"),
    )
    created_at = Column(
        DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP(0)")
    )

    @property
    def app_dataset_joins(self) -> list["AppDatasetJoin"]:
        """只读属性，获取配置的知识库关联记录"""
        return (
            db.session.query(AppDatasetJoin)
            .filter(AppDatasetJoin.app_id == self.app_id)
            .all()
        )


class AppConfigVersion(db.Model):
    """应用配置版本历史表，用于存储草稿配置+历史发布配置"""

    __tablename__ = "app_config_version"
    __table_args__ = (PrimaryKeyConstraint("id", name="pk_app_config_version_id"),)

    id = Column(
        UUID, nullable=False, server_default=text("uuid_generate_v4()")
    )  # 配置id
    app_id = Column(UUID, nullable=False)  # 关联应用id
    model_config = Column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )  # 模型配置
    dialog_round = Column(
        Integer, nullable=False, server_default=text("0")
    )  # 鞋带上下文轮数
    preset_prompt = Column(
        Text, nullable=False, server_default=text("''::text")
    )  # 人设与回复逻辑
    tools = Column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )  # 应用关联的工具列表
    workflows = Column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )  # 应用关联的工作流列表
    datasets = Column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )  # 应用关联的知识库列表
    retrieval_config = Column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )  # 检索配置
    long_term_memory = Column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )  # 长期记忆配置
    opening_statement = Column(
        Text, nullable=False, server_default=text("''::text")
    )  # 开场白文案
    opening_questions = Column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )  # 开场白建议问题列表
    speech_to_text = Column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )  # 语音转文本配置
    text_to_speech = Column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )  # 文本转语音配置
    suggested_after_answer = Column(
        JSONB,
        nullable=False,
        server_default=text("'{\"enable\": true}'::jsonb"),
    )  # 回答后生成建议问题
    review_config = Column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )  # 审核配置
    version = Column(Integer, nullable=False, server_default=text("0"))  # 发布版本号
    config_type = Column(
        String(255), nullable=False, server_default=text("''::character varying")
    )  # 配置类型
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(0)"),
        server_onupdate=text("CURRENT_TIMESTAMP(0)"),
    )
    created_at = Column(
        DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP(0)")
    )


class AppDatasetJoin(db.Model):
    """应用知识库关联表模型"""

    __tablename__ = "app_dataset_join"
    __table_args__ = (PrimaryKeyConstraint("id", name="pk_app_dataset_join_id"),)

    id = Column(UUID, nullable=False, server_default=text("uuid_generate_v4()"))
    app_id = Column(UUID, nullable=False)
    dataset_id = Column(UUID, nullable=False)
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(0)"),
        server_onupdate=text("CURRENT_TIMESTAMP(0)"),
    )
    created_at = Column(
        DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP(0)")
    )
