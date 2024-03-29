from sanic import Blueprint

from src.routers.api.auth import auth_b
from src.routers.api.fs import fs_b
from src.routers.api.share import share_b
from src.routers.api.storage import storage_b
from src.routers.api.upload_task import upload_task_b
from .setting import setting_b

api = Blueprint.group(
    fs_b,
    storage_b,
    upload_task_b,
    auth_b,
    share_b,
    setting_b,
    url_prefix="/api"
)


