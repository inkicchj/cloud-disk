import uuid
from uuid import uuid3, UUID

from voluptuous import Schema, Object, Required, In, Optional, All

from src.model.upload_task import UploadStatus, UploadMode
from .common import path_rule, name_rule, regular_path, operate_path


class NewUploadTaskSchema:
    def __init__(self, path, web_path, name, size, modified, mime_type, mode, wipe):
        self.path = path
        self.web_path = web_path
        self.name = name
        self.size = size
        self.modified = modified
        self.mime_type = mime_type
        self.mode = mode
        self.wipe = wipe


new_upload_task_schema = Schema(Object({
    Required("path", "路径不能为空"): All(
        path_rule,
        regular_path,
        operate_path
    ),
    Required("web_path", "源路径不能为空"): path_rule,
    Required("name", "名称不能为空"): name_rule,
    Required("size", "大小不能为空"): int,
    Required("modified", "修改日期不能为空"): int,
    Required("mime_type", "文件类型不能为空"): str,
    Required("mode"): In([UploadMode.STREAM.value, UploadMode.CHUNK.value]),
    Required("wipe"): bool
}, cls=NewUploadTaskSchema))


def generate_session_id(data: NewUploadTaskSchema) -> UUID:
    session_id = uuid3(
        namespace=uuid.NAMESPACE_OID,
        name=f"{data.name}_{data.size}_{data.modified}_{data.mime_type}"
    )
    return session_id


class UploadTaskListSchema:
    def __init__(self, status=None):
        self.status = status


upload_task_list_schema = Schema(Object({
    Optional("status"): In(container=[st.value for st in list(UploadStatus)]),
}, cls=UploadTaskListSchema))


class ClearTaskSchema:
    def __init__(self, status=None):
        self.status = status


clear_task_schema = Schema(Object({
    Required("status"): In(container=[UploadStatus.SUCCESS, UploadStatus.FAILED, UploadStatus.UPLOADING]),
}, cls=ClearTaskSchema))


class UploadTaskIDSchema:
    def __init__(self, session_id=None):
        self.session_id = session_id


upload_task_id_schema = Schema(Object({
    Required("session_id"): str
}, cls=UploadTaskIDSchema))
