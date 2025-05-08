import datetime
import hashlib
import uuid
from injector import inject
from dataclasses import dataclass
from qcloud_cos import CosConfig, CosS3Client
import os

from werkzeug.datastructures import FileStorage

from internal.entity.upload_file_entity import (
    ALLOWED_DOCUMENT_EXTENSION,
    ALLOWED_IMAGE_EXTENSION,
)
from internal.exception.exception import FailException
from internal.service import UploadFileService
from internal.model import Account


@inject
@dataclass
class CosService:
    """COS服务"""

    upload_file_service: UploadFileService

    def _get_client(self):
        """获取COS客户端"""
        conf = CosConfig(
            Region=os.getenv("COS_REGION"),
            SecretId=os.getenv("COS_SECRET_ID"),
            SecretKey=os.getenv("COS_SECRET_KEY"),
            Token=None,
            Scheme=os.getenv("COS_SCHEME", "https"),
        )
        return CosS3Client(conf)

    def _get_bucket(self):
        """获取COS Bucket"""
        return os.getenv("COS_BUCKET")

    def upload_file(self, file: FileStorage, only_image: bool, account: Account):
        """上传文件"""

        filename = file.filename
        extension = filename.rsplit(".", 1)[-1] if "." in filename else ""

        if extension.lower() not in (
            ALLOWED_DOCUMENT_EXTENSION + ALLOWED_IMAGE_EXTENSION
        ):
            raise FailException(f"不支持的文件类型: {extension}")
        elif only_image and extension.lower() not in ALLOWED_IMAGE_EXTENSION:
            raise FailException(f"不支持的文件类型: {extension}")

        client = self._get_client()
        bucket = self._get_bucket()
        random_filename = str(uuid.uuid4()) + "." + extension
        now = datetime.datetime.now()
        upload_filename = f"{now.year}/{now.month:02d}/{now.day:02d}/{random_filename}"

        file_content = file.stream.read()

        try:
            client.put_object(
                Bucket=bucket,
                Body=file_content,
                Key=upload_filename,
            )
        except Exception as e:
            raise FailException(f"上传文件失败: {str(e)}")

        return self.upload_file_service.create_upload_file(
            account_id=account.id,
            name=filename,
            key=upload_filename,
            size=len(file_content),
            extension=extension,
            mime_type=file.mimetype,
            hash=hashlib.sha3_256(file_content).hexdigest(),
        )

    def download_file(self, key: str, target_file_path: str):
        """下载文件"""
        client = self._get_client()
        bucket = self._get_bucket()

        client.download_file(
            Bucket=bucket,
            Key=key,
            DestFilePath=target_file_path,
        )

    @classmethod
    def get_file_url(cls, key: str):
        """获取文件URL"""
        cos_domain = os.getenv("COS_OS_DOMAIN")

        if not cos_domain:
            bucket = os.getenv("COS_BUCKET")
            scheme = os.getenv("COS_SCHEME", "https")
            region = os.getenv("COS_REGION")
            cos_domain = f"{scheme}://{bucket}.cos.{region}.myqcloud.com"

        return f"{cos_domain}/{key}"
