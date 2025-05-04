from sqlalchemy import (
    Column,
    UUID,
    String,
    Text,
    DateTime,
    PrimaryKeyConstraint,
    Index,
    text,
)

from internal.extension.database_extension import db


class App(db.Model):
    """AI应用基础模型类"""

    __tablename__ = "app"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_app_id"),
        Index("idx_app_account_id", "account_id"),
    )

    id = Column(UUID, server_default=text("uuid_generate_v4()"), nullable=False)
    account_id = Column(UUID)
    name = Column(
        String(255), server_default=text("''::character varying"), nullable=False
    )
    icon = Column(
        String(255), server_default=text("''::character varying"), nullable=False
    )
    description = Column(Text, server_default=text("''::text"), nullable=False)
    status = Column(
        String(255), server_default=text("''::character varying"), nullable=False
    )
    updated_at = Column(
        DateTime,
        server_default=text("CURRENT_TIMESTAMP(0)"),
        server_onupdate=text("CURRENT_TIMESTAMP(0)"),
        nullable=False,
    )
    created_at = Column(
        DateTime, server_default=text("CURRENT_TIMESTAMP(0)"), nullable=False
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
