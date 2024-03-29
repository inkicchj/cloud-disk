from enum import Enum
from typing import Type, Optional

from pydantic import BaseModel
from tortoise import Model, fields, BaseDBAsyncClient
from tortoise.signals import post_delete

from src.utils.filesystem import VFS


class UploadStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    UPLOADING = "UPLOADING"


class UploadMode(str, Enum):
    STREAM = "STREAM"
    CHUNK = "CHUNK"


class ChunkInfo(BaseModel):
    chunk_size: int
    chunk_total: int
    chunk_cur: int


class UploadTask(Model):
    id = fields.IntField(pk=True)
    session_id = fields.CharField(index=True, unique=True, null=False, max_length=256, description="上传唯一标识")
    path = fields.CharField(null=False, max_length=200, description="保存路径")
    web_path = fields.CharField(null=False, max_length=200, description="网络路径")
    name = fields.CharField(null=False, max_length=200, description="文件名")
    size = fields.IntField(description="文件大小")
    modified = fields.IntField(description="修改时间")
    mime_type = fields.CharField(max_length=100, description="文件类型")
    status = fields.CharEnumField(UploadStatus, description="任务状态")
    mode = fields.CharEnumField(UploadMode, description="任务模式: 流式上传/分片上传")
    wipe = fields.BooleanField(description="是否覆盖已有文件")
    chunk_info = fields.JSONField(null=True, default=None, description="存储分片信息")


@post_delete(UploadTask)
async def upload_task_post_delete(
        sender: "Type[UploadTask]", instance: UploadTask, using_db: "Optional[BaseDBAsyncClient]"
) -> None:
    if instance.status != UploadStatus.SUCCESS:
        sub = VFS.opendir(instance.path)
        if sub.exists(instance.name):
            sub.remove(instance.name)
