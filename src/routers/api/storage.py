import asyncio
from pathlib import Path

from fs.osfs import OSFS
from fs.path import forcedir, abspath, normpath
from sanic import Request, HTTPResponse, json, Blueprint

from src.model.storage import Storage, OrderBy
from src.model.user import Role
from src.routers.resp import Resp
from src.schemas.storage import new_storage_schema, NewStorageSchema
from src.schemas.storage import storage_id_schema, StorageIDSchema
from src.schemas.storage import update_storage_schema, UpdateStorageSchema
# 数据校验
from src.schemas.validator import validate
from src.utils.authenticator import token_required
from src.utils.filesystem import VFS
from src.utils.filesystem.osfs import OSVFS

storage_b = Blueprint("Storage", url_prefix="/storage")


@storage_b.post("/order_field")
@token_required(allow=[Role.Admin])
async def order_field(request: Request, token) -> HTTPResponse:
    return json(Resp.ok_data([ob.value for ob in list(OrderBy)]))


@storage_b.post("/create")
@token_required(allow=[Role.Admin])
@validate(json=(new_storage_schema, NewStorageSchema))
async def create(request: Request, body: NewStorageSchema, token) -> HTTPResponse:

    s = await Storage.get_or_none(mount_name=body.mount_name)
    if s:
        return json(Resp.err_msg(f"挂载名称已存在: {body.mount_name}"))
    root_path = Path(body.root_path).absolute()

    root_fs = OSVFS(str(root_path), create=True)

    space_size = root_fs.get_dir_size("/")[0]
    if space_size > body.capacity:
        return json(Resp.err_msg(f"系统文件夹大小超过存储空间容量: {space_size}>{body.capacity}"))

    r: Storage = await Storage.create(
        mount_name=body.mount_name,
        root_path=body.root_path,
        order=body.order,
        capacity=body.capacity,
        order_field=body.order_field,
        reverse=body.reverse
    )
    if r.activated:
        VFS.mount(r.mount_name, root_fs)

    return json(Resp.ok_msg(f"创建存储空间成功: {body.mount_name}"))


@storage_b.post("/list")
@token_required(allow=[Role.Admin])
async def get_list(request: Request, token) -> HTTPResponse:
    storages = await Storage.filter().order_by("order").values()

    async def calculate_size(s):
        if s['activated']:
            s["space_size"] = VFS.get_dir_size(s["mount_name"])[0]
        else:
            s["space_size"] = 0
        return s

    tasks = [calculate_size(s) for s in storages]
    result = await asyncio.gather(*tasks)
    data = sorted(result, key=lambda x: x['order'])
    return json(Resp.ok_data(data))


@storage_b.post("/update")
@token_required(allow=[Role.Admin])
@validate(json=(update_storage_schema, UpdateStorageSchema))
async def update(request: Request, body: UpdateStorageSchema, token) -> HTTPResponse:

    storage_ = await Storage.get_or_none(id=body.id)
    if not storage_:
        return json(Resp.err_msg("存储空间不存在"))

    has_name = await Storage.get_or_none(mount_name=body.mount_name, id__not_in=[body.id])
    if has_name:
        return json(Resp.err_msg(f"挂在名称已存在: {body.mount_name}"))

    root_path = Path(body.root_path).absolute()
    if not root_path.is_dir():
        return json(Resp.err_msg(f"系统文件夹不存在: {root_path}"))

    root_fs = OSVFS(str(root_path), create=True)
    space_size = root_fs.get_dir_size("/")[0]
    if space_size > body.capacity:
        return json(Resp.err_msg(f"系统文件夹大小超过存储空间容量: {space_size}>{body.capacity}"))

    await Storage.filter(id=body.id).update(
        mount_name=body.mount_name,
        root_path=body.root_path,
        order=body.order,
        capacity=body.capacity,
        order_field=body.order_field,
        reverse=body.reverse
    )

    if storage_.activated:
        mount_path = forcedir(abspath(normpath(storage_.mount_name)))
        VFS.unmount(mount_path)
        VFS.mount(body.mount_name, root_fs)

    return json(Resp.ok_msg("更新存储空间成功"))


@storage_b.post("/info")
@token_required(allow=[Role.Admin])
@validate(json=(storage_id_schema, StorageIDSchema))
async def info(request: Request, body: StorageIDSchema, token) -> HTTPResponse:
    storage_ = await Storage.get_or_none(id=body.id).values()
    if not storage_:
        return json(Resp.err_msg("存储空间不存在"))
    return json(Resp.ok_data(storage_))


@storage_b.post("/enable")
@token_required(allow=[Role.Admin])
@validate(json=(storage_id_schema, StorageIDSchema))
async def enable(request: Request, body: StorageIDSchema, token) -> HTTPResponse:
    storage_ = await Storage.get_or_none(id=body.id)
    if not storage_:
        return json(Resp.err_msg("存储空间不存在"))
    await Storage.filter(id=body.id).update(activated=True)
    VFS.mount(storage_.mount_name, OSFS(storage_.root_path, create=True))
    return json(Resp.ok_msg(f"激活存储空间成功: {storage_.mount_name}"))


@storage_b.post("/disable")
@token_required(allow=[Role.Admin])
@validate(json=(storage_id_schema, StorageIDSchema))
async def disable(request: Request, body: StorageIDSchema, token) -> HTTPResponse:
    storage_ = await Storage.get_or_none(id=body.id)
    if not storage_:
        return json(Resp.err_msg("存储空间不存在"))
    await Storage.filter(id=body.id).update(activated=False)
    VFS.unmount(storage_.mount_name)
    return json(Resp.ok_msg(f"关闭存储空间成功: {storage_.mount_name}"))


@storage_b.post("/delete")
@token_required(allow=[Role.Admin])
@validate(json=(storage_id_schema, StorageIDSchema))
async def delete(request: Request, body: StorageIDSchema, token) -> HTTPResponse:
    storage_ = await Storage.get_or_none(id=body.id)
    if storage_:
        VFS.unmount(storage_.mount_name)
        await storage_.delete()
    return json(Resp.ok_msg(f"删除存储空间成功: {storage_.mount_name}"))
