import mimetypes
from datetime import datetime
from pathlib import Path
from typing import Union

import shortuuid
from sanic import Request, json, Blueprint, response
from sanic.compat import stat_async
from sanic.handlers import ContentRangeHandler

from config import AppConfig
from config import PaginationMode
from src.model.share import Share, Expired
from src.model.storage import Storage
from src.model.user import Role
from src.routers.api.fs import FInfo
from src.routers.resp import Resp
from src.schemas.share import list_share_schema, ListShareSchema
from src.schemas.share import new_share_schema, NewShareSchema
from src.schemas.share import public_share_schema, PublicShareSchema
from src.schemas.share import share_id_schema, ShareIDSchema
from src.schemas.validator import validate
from src.utils.authenticator import token_required
from src.utils.filesystem import VFS, hum_convert
from src.utils.thumbnail import get_thumbnail, set_thumbnail

share_b = Blueprint("Share", url_prefix="/share")


# 创建分享链接
@share_b.post("/create")
@token_required(allow=[Role.Admin])
@validate(json=(new_share_schema, NewShareSchema))
async def create(request: Request, body: NewShareSchema, token):
    if str(body.path).endswith("/"):
        body.path = body.path[:-1]
    if not VFS.exists(body.path):
        return json(Resp.err_msg(f"文件/文件夹不存在: {body.path}"))

    namespaces = f"{body.path}_{str(datetime.now().timestamp())}"
    mark = shortuuid.uuid(name=namespaces)

    def get_expired():
        for e in list(Expired):
            if e.name == body.expired:
                if e == Expired.Forever:
                    return e.value
                else:
                    return datetime.now().timestamp() + e.value

    await Share.create(
        mark=mark,
        path=body.path,
        password=body.password,
        expired=get_expired(),
        is_dir=VFS.getinfo(body.path).is_dir
    )
    return json(Resp.ok_msg("创建分享链接成功"))


# 获取分享列表
@share_b.post("/list")
@token_required(allow=[Role.Admin])
@validate(json=(list_share_schema, ListShareSchema))
async def lists(request: Request, body: ListShareSchema, token):
    shares = await Share.filter().offset(
        (body.page - 1) * AppConfig.config.fs.pagination_size).limit(AppConfig.config.fs.pagination_size).order_by(
        "-id").values()
    total = await Share.all().count()
    return json(Resp.ok_data(Resp.paginate(body.page, total, shares, mode=PaginationMode.Manual.value)))


# 获取分享信息
@share_b.post("/info")
@token_required(allow=[Role.Admin])
@validate(json=(share_id_schema, ShareIDSchema))
async def info(request: Request, body: ShareIDSchema, token):
    share = await Share.get_or_none(id=body.id).values()
    if not share:
        return json(Resp.err_msg("该分享链接不存在"))
    return json(Resp.ok_data(share))


# 删除分享链接
@share_b.post("/delete")
@token_required(allow=[Role.Admin])
@validate(json=(share_id_schema, ShareIDSchema))
async def delete(request: Request, body: ShareIDSchema, token):
    share = await Share.get_or_none(id=body.id)
    if share:
        await share.delete()
    return json(Resp.ok_msg("删除分享链接成功"))


# 获取过期
@share_b.post("/expired")
@token_required(allow=[Role.Admin])
async def get_expired(request: Request, token):
    return json(Resp.ok_data([e.name for e in list(Expired)]))


# 访问分享内容
@share_b.post("/view")
@validate(json=(public_share_schema, PublicShareSchema))
async def view_share(request: Request, body: PublicShareSchema):
    share = await Share.get_or_none(mark=body.mark)
    if not share:
        return json(Resp.err(51100, None, "分享已取消"))
    if share.expired < datetime.now().timestamp() and share.expired != Expired.Forever.value:
        return json(Resp.err(51101, None, "分享已过期"))
    if share.password and share.password != body.password:
        return json(Resp.err(51102, None, "访问码错误"))
    if share.is_dir:
        dir_path = share.path + body.path
        if not VFS.exists(dir_path):
            return json(Resp.err_msg(f"分享不存在"))
        if VFS.isdir(dir_path):
            file_list = list()
            for entry in VFS.scandir(dir_path, namespaces=["basic", "details"]):
                if not entry.is_dir:
                    if AppConfig.config.preview.thumbnail:
                        syspath = VFS.getsyspath(dir_path + entry.name)
                        thumb = await get_thumbnail(syspath)
                        if thumb is None:
                            request.app.add_task(set_thumbnail(syspath))
                    else:
                        thumb = None
                else:
                    thumb = None
                entry_ = FInfo(
                    name=entry.name,
                    size=entry.size,
                    is_dir=entry.is_dir,
                    modified=entry.modified.timestamp(),
                    file_type=mimetypes.guess_type(entry.name)[0],
                    raw_path=None,
                    parent_dir=None,
                    thumbnail=thumb
                )
                file_list.append(entry_.model_dump())
            mount_name = dir_path.split("/")[1]
            storage = await Storage.get(mount_name=mount_name, activated=True)
            if not storage.reverse:
                file_list.sort(key=lambda r: (-r["is_dir"], r[storage.order_field]))
            else:
                file_list.sort(key=lambda r: (r["is_dir"], r[storage.order_field]), reverse=True)
            return json(Resp.ok_data(file_list))
        else:
            f = VFS.getinfo(dir_path, namespaces=["basic", "details"])
            if AppConfig.config.preview.thumbnail:
                syspath = VFS.getsyspath(dir_path)
                thumb = await get_thumbnail(syspath)
                if thumb is None:
                    request.app.add_task(set_thumbnail(syspath))
            else:
                thumb = None
            v = FInfo(
                name=f.name,
                size=f.size,
                is_dir=f.is_dir,
                modified=f.modified.timestamp(),
                file_type=mimetypes.guess_type(f.name)[0],
                raw_path=None,
                parent_dir=None,
                thumbnail=thumb
            )
            return json(Resp.ok_data([v.model_dump()]))
    else:
        if not VFS.exists(share.path):
            return json(Resp.err_msg("分享不存在"))
        f = VFS.getinfo(share.path, namespaces=["basic", "details"])
        if AppConfig.config.preview.thumbnail:
            syspath = VFS.getsyspath(share.path)
            thumb = await get_thumbnail(syspath)
            if thumb is None:
                request.app.add_task(set_thumbnail(syspath))
        else:
            thumb = None
        v = FInfo(
            name=f.name,
            size=f.size,
            is_dir=f.is_dir,
            modified=f.modified.timestamp(),
            file_type=mimetypes.guess_type(f.name)[0],
            raw_path=None,
            parent_dir=None,
            thumbnail=thumb
        )
        return json(Resp.ok_data([v.model_dump()]))


@share_b.get("/source")
@validate(query=(public_share_schema, PublicShareSchema))
async def share_download(request: Request, query: PublicShareSchema):
    share = await Share.get_or_none(mark=query.mark[0])
    if not share:
        return json(Resp.err(51100, None, "分享已取消"))
    if share.expired < datetime.now().timestamp() and share.expired != Expired.Forever.value:
        return json(Resp.err(51101, None, "分享已过期"))
    if share.password and share.password != query.password:
        return json(Resp.err(51102, None, "访问码错误"))
    if share.is_dir:
        share_path = share.path + query.path
        share_path = share_path if not str(share_path).endswith("/") else share_path[:-1]
    else:
        share_path = share.path
    if not VFS.exists(share_path):
        return json(Resp.err_msg("分享文件不存在"))
    if VFS.isdir(share_path):
        return json(Resp.err_msg("文件夹无法下载"))
    if VFS.getsize(share_path) > AppConfig.config.fs.max_download_size:
        return json(Resp.err_msg(f"下载文件的大小不能超过{hum_convert(AppConfig.config.fs.max_download_size)}"))

    meta = {
        "location": VFS.getsyspath(share_path),
        "chunk_size": 1024 * 1024 * 2,
        "mime_type": mimetypes.guess_type(share_path)[0],
        "headers": {
            "Content-Disposition": f'Attachment; filename="{Path(share_path).name}"',
            "X-File-Type": mimetypes.guess_type(share_path)[0],
        },
        "_range": None,
    }
    range_span: Union[str, None] = request.headers.get("Range")
    if range_span:
        stat = await stat_async(share_path)
        _range = ContentRangeHandler(request, stat)
        meta["_range"] = _range
    return await response.file_stream(**meta)
