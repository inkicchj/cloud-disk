import mimetypes
import os
import re
import stat
from datetime import datetime
from pathlib import Path
from typing import Union

import shortuuid
from aiofiles import os as async_os
from pydantic import BaseModel
from repro_zipfile import ReproducibleZipFile
from sanic import Blueprint, Request, HTTPResponse, json, empty
from sanic.compat import stat_async
from sanic.handlers import ContentRangeHandler
from sanic.response import file_stream
from voluptuous.error import Invalid

from config import AppConfig, PaginationMode
from fs.subfs import SubFS
from src.model.storage import Storage
from src.model.user import Role
from src.routers.resp import Resp
from src.routers.resp import file_stream as my_file_stream
# 工具函数
from src.schemas.fs import action_path_schema, ActionPathSchema
from src.schemas.fs import copy_and_move_schema, CopyAndMoveSchema
from src.schemas.fs import lists_schema, ListsSchema
from src.schemas.fs import name_list_one_dir_schema, NameListOneDirSchema
from src.schemas.fs import path_schema, PathSchema
from src.schemas.fs import search_schema, SearchSchema
# 数据校验
from src.schemas.validator import validate as validate
from src.utils.authenticator import token_required
from src.utils.filesystem import VFS
from src.utils.filesystem import hum_convert
from src.utils.thumbnail import get_thumbnail, set_thumbnail

fs_b = Blueprint("FS", url_prefix="/fs")


class FInfo(BaseModel):
    name: str
    size: Union[int, None]
    is_dir: bool
    modified: float
    file_type: Union[str, None]
    raw_path: Union[str, None]
    parent_dir: Union[str, None]
    thumbnail: Union[str, None] = None


# 列出目录列表
@fs_b.post("/list")
@token_required(allow=[Role.Admin])
@validate(json=(lists_schema, ListsSchema))
async def lists(
        request: Request, body: ListsSchema, token
) -> HTTPResponse:
    file_list = list()

    for entry in VFS.scandir(body.path, namespaces=["basic", "details"]):
        if not entry.is_dir:
            syspath = VFS.opendir(body.path).getsyspath(entry.name)
            # 如果文件无法写入，则设置写入权限
            if not os.access(syspath, os.W_OK):
                os.chmod(syspath, stat.S_IWRITE)
            if AppConfig.config.preview.thumbnail:
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
            raw_path=body.path + entry.name,
            parent_dir=body.path,
            thumbnail=thumb
        )
        file_list.append(entry_.model_dump())

    if body.path != "/":
        mount_name = body.path.split("/")[1]
        storage = await Storage.get(mount_name=mount_name, activated=True)
        if not storage.reverse:
            file_list.sort(key=lambda r: (-r["is_dir"], r[storage.order_field]))
        else:
            file_list.sort(key=lambda r: (r["is_dir"], r[storage.order_field]), reverse=True)

    return json(Resp.ok_data(Resp.paginate(body.page, len(file_list), file_list, PaginationMode.All.value)))


# 获取目录下所有文件
@fs_b.post("/files")
@token_required(allow=[Role.Admin])
@validate(json=(path_schema, PathSchema))
async def get_files(request: Request, body: PathSchema, token):
    file_list = []
    for entry in VFS.walk.info(body.path, namespaces=["basic", "details"]):
        path_ = entry[0]
        info_ = entry[1]
        if not info_.is_dir:
            if AppConfig.config.preview.thumbnail:
                syspath = VFS.getsyspath(path_)
                thumb = await get_thumbnail(syspath)
            else:
                thumb = None
            entry_ = FInfo(
                name=info_.name,
                size=info_.size,
                is_dir=info_.is_dir,
                modified=info_.modified.timestamp(),
                file_type=mimetypes.guess_type(info_.name)[0],
                raw_path=path_,
                parent_dir=path_[0:len(path_) - len(info_.name)],
                thumbnail=thumb
            )
            file_list.append(entry_.model_dump())
        else:
            continue
    return json(Resp.ok_data(file_list))


# 列出目录列表
@fs_b.post("/dirs")
@token_required(allow=[Role.Admin])
@validate(json=(lists_schema, ListsSchema))
async def dirs(
        request: Request, body: ListsSchema, token
) -> HTTPResponse:
    file_list = list()
    for entry in VFS.scandir(body.path, namespaces=["basic", "details"]):
        if entry.is_dir:
            entry_ = FInfo(
                name=entry.name,
                size=entry.size,
                is_dir=entry.is_dir,
                modified=entry.modified.timestamp(),
                file_type=None,
                raw_path=body.path + entry.name,
                parent_dir=body.path,
                thumbnail=None
            )
            file_list.append(entry_.model_dump())
        else:
            continue

    if body.path != "/":
        mount_name = body.path.split("/")[1]
        storage = await Storage.get(mount_name=mount_name, activated=True)
        if not storage.reverse:
            file_list.sort(key=lambda r: (-r["is_dir"], r[storage.order_field]))
        else:
            file_list.sort(key=lambda r: (r["is_dir"], r[storage.order_field]), reverse=True)

    return json(Resp.ok_data(Resp.paginate(body.page, len(file_list), file_list, PaginationMode.All.value)))


# 新建文件夹
@fs_b.post("/mkdir")
@token_required(allow=[Role.Admin])
@validate(json=(action_path_schema, ActionPathSchema))
async def mkdir(
        request: Request, body: ActionPathSchema, token
) -> HTTPResponse:
    path_ = body.path + body.name
    VFS.makedirs(path_)
    entry = VFS.getinfo(path_, namespaces=['basic', 'details'])

    entry_ = FInfo(
        name=entry.name,
        size=entry.size,
        is_dir=entry.is_dir,
        modified=entry.modified.timestamp(),
        file_type=None,
        raw_path=body.path + entry.name,
        parent_dir=body.path,
        thumbnail=None
    )

    return json(Resp.ok_data(entry_.model_dump()))


# 重命名文件/文件夹
@fs_b.post("/rename")
@token_required(allow=[Role.Admin])
@validate(json=(action_path_schema, ActionPathSchema))
async def rename(request: Request, body: ActionPathSchema, token) -> HTTPResponse:
    path_ = body.path
    old_sys_path = VFS.getsyspath(path_)

    new_sys_path = Path(old_sys_path).parent.joinpath(body.name)
    if new_sys_path.exists():
        return json(Resp.err_msg(f"路径'{path_}'中已有同名文件/文件夹"))

    await async_os.rename(old_sys_path, new_sys_path)

    return json(Resp.ok_msg(f"重命名文件/文件夹成功"))


# 获取文件/文件夹信息
@fs_b.post("/detail")
@token_required(allow=[Role.Admin])
@validate(json=(path_schema, PathSchema))
async def detail(request: Request, body: PathSchema, token) -> HTTPResponse:
    entry = VFS.getinfo(body.path, ["basic", "details"])
    if not entry.is_dir:
        syspath = VFS.getsyspath(body.path)
        thumb = await get_thumbnail(syspath)
    else:
        thumb = None

    entry_ = FInfo(
        name=entry.name,
        size=VFS.getsize(body.path) if not entry.is_dir else VFS.get_dir_size(body.path)[0],
        is_dir=entry.is_dir,
        modified=entry.modified.timestamp(),
        file_type=mimetypes.guess_type(entry.name)[0],
        raw_path=body.path,
        parent_dir=body.path[0:len(body.path) - len(entry.name)],
        thumbnail=thumb
    )

    return json(Resp.ok_data(entry_.model_dump()))


# 移动文件/文件夹
@fs_b.post("/move")
@token_required(allow=[Role.Admin])
@validate(json=(copy_and_move_schema, CopyAndMoveSchema))
async def move(request: Request, body: CopyAndMoveSchema, token) -> HTTPResponse:
    dist_mount_name = body.dst_dir.split("/")[1]
    src_mount_name = body.src_dir.split("/")[1]
    if dist_mount_name != src_mount_name:
        storage = await Storage.get_or_none(mount_name=dist_mount_name, activated=True)
        if not storage:
            raise Invalid(f"路径不存在: {body.dst_dir}")

        files_size = 0
        for n in body.name:
            p = body.src_dir + n
            files_size += VFS.getsize(p) if not VFS.isdir(p) else VFS.get_dir_size(p)[0]

        dst_size = files_size + VFS.get_dir_size("/" + storage.mount_name)[0]
        if dst_size > storage.capacity:
            return json(Resp.err_msg(f"存储空间容量不足: {hum_convert(storage.capacity)}"))

    for n in body.name:
        src_path = body.src_dir + n
        dst_path = body.dst_dir + n
        if VFS.isdir(src_path):
            VFS.movedir(src_path, dst_path, True)
        else:
            VFS.move(src_path, dst_path, True)
    return json(Resp.ok_msg("移动文件/文件夹成功"))


# 复制文件/文件夹
@fs_b.post("/copy")
@token_required(allow=[Role.Admin])
@validate(json=(copy_and_move_schema, CopyAndMoveSchema))
async def copy(request: Request, body: CopyAndMoveSchema, token) -> HTTPResponse:
    dist_mount_name = body.dst_dir.split("/")[1]
    storage = await Storage.get_or_none(mount_name=dist_mount_name, activated=True)
    if not storage:
        raise Invalid(f"路径不存在: {body.dst_dir}")

    files_size = 0
    for n in body.name:
        p = body.src_dir + n
        files_size += VFS.getsize(p) if not VFS.isdir(p) else VFS.get_dir_size(p)[0]

    dst_size = files_size + VFS.get_dir_size("/" + storage.mount_name)[0]
    if dst_size > storage.capacity:
        return json(Resp.err_msg(f"存储空间容量不足: {hum_convert(storage.capacity)}"))

    for n in body.name:
        src_path = body.src_dir + n
        dst_path = body.dst_dir + n
        if VFS.isdir(src_path):
            VFS.copydir(src_path, dst_path, True)
        else:
            VFS.copy(src_path, dst_path, True)
    return json(Resp.ok_msg("复制文件/文件夹成功"))


# 清理空文件夹
@fs_b.post("/clear_empty_dir")
@token_required(allow=[Role.Admin])
@validate(json=(path_schema, PathSchema))
async def clear_empty_dir(request: Request, body: PathSchema, token) -> HTTPResponse:
    sub_fs: SubFS = VFS.opendir(body.path)
    for s in sub_fs.walk():
        if not sub_fs.exists(s.path):
            continue
        if sub_fs.isempty(s.path):
            try:
                sub_fs.removedir(s.path)
            except Exception as e:
                continue

    return json(Resp.ok_msg(f"清理空文件夹成功: {body.path}"))


# 删除文件/文件夹
@fs_b.post("/remove")
@token_required(allow=[Role.Admin])
@validate(json=(name_list_one_dir_schema, NameListOneDirSchema))
async def remove(request: Request, body: NameListOneDirSchema, token) -> HTTPResponse:
    for n in body.name:
        if VFS.isdir(body.src_dir + n):
            VFS.removetree(body.src_dir + n)
        else:
            VFS.remove(body.src_dir + n)
    return json(Resp.ok_msg("删除文件/文件夹成功"))


# 下载或预览资源
@fs_b.get("/source")
@token_required(allow=[Role.Admin])
@validate(query=(path_schema, PathSchema))
async def download(request: Request, query: PathSchema, token):
    skip_files = re.split(r"[,，]", AppConfig.config.fs.skip_files)
    if Path(query.path).name in skip_files:
        return json(Resp.err_msg(f"'{Path(query.path).name}'是受保护文件,跳过下载"))
    size = VFS.getsize(query.path) if not VFS.isdir(query.path) else VFS.get_dir_size(query.path)[0]
    if size > AppConfig.config.fs.max_download_size:
        return json(Resp.err_msg(f"下载资源大小不能超过{hum_convert(AppConfig.config.fs.max_download_size)}"))
    if VFS.getinfo(query.path).is_dir:
        zip_path = Path("temp").joinpath(
            shortuuid.uuid(name=f"{query.path}_{str(datetime.now())}") + ".zip"
        ).absolute()
        if not zip_path.exists():
            with ReproducibleZipFile(
                    zip_path,
                    "w"
            ) as zp:
                path_ = str(query.path[0:-1]).split("/")[-1]
                for f in VFS.walk.files(query.path):
                    name = VFS.getsyspath(f)
                    zp.write(filename=name, arcname=f.replace(path_, ""))
            zp.close()
        src_path = zip_path
    else:
        src_path = VFS.getsyspath(query.path)

    file = await async_os.stat(src_path)
    meta = {
        "location": src_path,
        "chunk_size": 1024 * 1024 * 2,
        "mime_type": mimetypes.guess_type(src_path)[0],
        "headers": {
            "X-File-Length": str(file.st_size),
            "Content-Disposition": f'Attachment; filename="{Path(src_path).name}"',
            "Content-Type": mimetypes.guess_type(src_path)[0],
        },
        "_range": None,
        "del_file": True if VFS.getinfo(query.path).is_dir else False
    }
    range_span: Union[str, None] = request.headers.get("Range")
    if range_span:
        stat_ = await stat_async(src_path)
        _range = ContentRangeHandler(request, stat_)
        meta["_range"] = _range

    return await my_file_stream(**meta)


# 搜索文件
@fs_b.post("/search")
@token_required(allow=[Role.Admin])
@validate(json=(search_schema, SearchSchema))
async def search(request: Request, body: SearchSchema, token):
    rs = []
    if body.is_dir:
        data = list(VFS.walk.dirs(body.path, filter_dirs=[body.name]))
    else:
        data = list(VFS.walk.files(body.path, filter=[body.name]))
    for p in data:
        info = VFS.getinfo(p, namespaces=["basic", "details"])
        rs.append({
            "name": info.name,
            "parent_dir": p[0: len(p) - len(info.name)],
            "size": info.size,
            "is_dir": info.is_dir
        })
    return json(Resp.ok_data(Resp.paginate(body.page, len(rs), rs, PaginationMode.Manual.value)))


# 获取缩略图
@fs_b.get("/thumbnail/<year:int>/<month:int>/<ident:str>")
async def thumb_handler(
        request: Request, year: int, month: int, ident: str
):
    path = Path("data/thumbnail").absolute().joinpath(str(year)).joinpath(str(month)).joinpath(ident)
    if path.exists():
        return await file_stream(
            path,
            chunk_size=1024 * 1024 * 2,
            mime_type=mimetypes.guess_type(path)[0],
            headers={
                "Content-Disposition": f'filename="{ident}"',
                "Content-Type": mimetypes.guess_type(path)[0],
            },
        )
    return empty()
