from typing import Optional

from sanic import Blueprint, Request, HTTPResponse, json

from config import AppConfig
from fs.path import forcedir, abspath, normpath
from fs.subfs import SubFS
from src.model.storage import Storage
from src.model.upload_task import UploadTask, UploadStatus, UploadMode, ChunkInfo
from src.model.user import Role
from src.routers.resp import Resp
from src.routers.tools import cancel_task
from src.schemas.upload_task import clear_task_schema, ClearTaskSchema
from src.schemas.upload_task import generate_session_id
from src.schemas.upload_task import new_upload_task_schema, NewUploadTaskSchema
from src.schemas.upload_task import upload_task_id_schema, UploadTaskIDSchema
# 数据校验
from src.schemas.validator import validate
from src.utils.authenticator import token_required
from src.utils.cache_store import MemCache
from src.utils.filesystem import VFS
from src.utils.filesystem import hum_convert
from src.utils.thumbnail import set_thumbnail

upload_task_b = Blueprint('UploadTaskB', url_prefix='/upload_task')


# 创建上传任务
@upload_task_b.post("/create")
@token_required(allow=[Role.Admin])
@validate(json=(new_upload_task_schema, NewUploadTaskSchema))
async def upload_task(request: Request, body: NewUploadTaskSchema, token) -> HTTPResponse:
    if body.size > AppConfig.config.fs.max_upload_size:
        return json(Resp.err(52001, None,
                             f"文件大小不能超过{hum_convert(AppConfig.config.fs.max_upload_size)}"))

    mount_name = body.path.split("/")[1]
    storage = await Storage().get_or_none(mount_name=mount_name, activated=True)
    if not storage:
        return json(Resp.err(52001, None, "存储空间不存在"))
    if (int(body.size) + VFS.get_dir_size(body.path)[0]) > storage.capacity:
        return json(Resp.err(52001, None, "存储空间容量不足"))

    session_id = str(generate_session_id(body))
    task: Optional[dict] = await UploadTask.get_or_none(session_id=session_id).values()

    if task:
        sub_fs: SubFS = VFS.opendir(task['path'])
        if not sub_fs.exists(task['name']):
            uploaded = 0
        else:
            uploaded = sub_fs.getsize(task['name'])
        task['uploaded'] = uploaded
        return json(Resp.ok_data(task))
    else:
        web_path = forcedir(abspath(normpath(body.web_path)))[:-1]
        name_ = abspath(normpath(body.name))
        sub_fs: SubFS = VFS.opendir(body.path)
        create_folder = True if web_path != name_ else False
        if create_folder:
            if not web_path.endswith(name_):
                return json(Resp.err_msg(f"上传文件源路径'{web_path}'与名称'{body.name}'不匹配"))
            parent_dir = web_path[:-len(body.name)]
            if not sub_fs.exists(parent_dir):
                sub_fs.makedirs(parent_dir)
            sub_fs = sub_fs.opendir(parent_dir)
            body.path = forcedir(normpath(body.path + parent_dir))
        else:
            sub_fs = sub_fs

        if body.mode == UploadMode.STREAM.value:
            chunk_info = None
        elif body.mode == UploadMode.CHUNK.value:
            chunk_size = AppConfig.config.fs.chunk_size
            if body.size <= chunk_size:
                chunk_total = 1
            else:
                chunk_total = 0
                if body.size / chunk_size > body.size // chunk_size:
                    chunk_total += int(body.size / chunk_size) + 1
                else:
                    chunk_total += int(body.size / chunk_size)
            chunk_info = ChunkInfo(chunk_size=chunk_size, chunk_total=chunk_total, chunk_cur=0).model_dump()
        else:
            return json(Resp.err_msg(f"不正确的上传模式: ${body.mode}"))

        result = sub_fs.create(name_, wipe=body.wipe)
        if not result:
            return json(Resp.err_msg(f"该路径已存在同名文件: {body.name}"))

        await UploadTask.create(
            session_id=session_id,
            path=body.path,
            web_path=web_path,
            name=body.name,
            size=body.size,
            mime_type=body.mime_type,
            modified=body.modified,
            status=UploadStatus.UPLOADING,
            mode=body.mode,
            wipe=body.wipe,
            chunk_info=chunk_info
        )
        task_ = await UploadTask.get(session_id=session_id).values()
        task_['uploaded'] = 0
        return json(Resp.ok_data(task_))


# 流式上传文件
@upload_task_b.post("/stream/<session_id:str>/", stream=True)
@token_required(allow=[Role.Admin])
async def upload_task_stream(request, session_id: str, token) -> HTTPResponse:
    task = await UploadTask.get_or_none(session_id=session_id).values()
    if not task:
        return json(Resp.err(52001, None, f"上传任务不存在: {session_id}"))
    if task['mode'] != UploadMode.STREAM.value:
        return json(Resp.err(52001, None, f"上传模式不匹配,请删除任务后重新上传"))
    sub_fs: SubFS = VFS.opendir(task['path'])

    # 失败可以重试
    if task['status'] == UploadStatus.FAILED:
        task['status'] = UploadStatus.UPLOADING
        await UploadTask.filter(session_id=session_id).update(status=UploadStatus.UPLOADING)

    if task['status'] != UploadStatus.UPLOADING:
        task['uploaded'] = sub_fs.getsize(task['name'])
        return json(Resp.ok_data(task))

    # 记录任务
    record_task = await MemCache.get_data(f"upload_{session_id}")
    if record_task is None:
        await MemCache.set_data(f"upload_{session_id}", task['id'])
    try:
        read_size = 0
        while True:
            body = await request.stream.read()
            record_task = await MemCache.get_data(f"upload_{session_id}")
            if record_task is None:
                try:
                    if sub_fs.exists(task['name']):
                        sub_fs.remove(task['name'])
                except:
                    pass
                await UploadTask.filter(session_id=session_id).delete()
                return json(Resp.err(52001, None, f"任务已取消"))
            if body is None:
                break
            read_size += len(body)
            real_size = sub_fs.getsize(task['name'])
            if read_size > real_size:
                sub_size = read_size - real_size
                if sub_size < len(body):
                    body = body[len(body) - sub_size:]
                sub_fs.appendbytes(task['name'], body)
            else:
                continue
        task['status'] = UploadStatus.SUCCESS
        await MemCache.del_data(f"upload_{session_id}")
        # 创建缩略图
        if AppConfig.config.preview.thumbnail:
            request.app.add_task(set_thumbnail(sub_fs.getsyspath(task['name'])))
    except Exception as e:
        task['status'] = UploadStatus.FAILED
    await UploadTask.filter(session_id=session_id).update(status=task['status'])
    task['uploaded'] = sub_fs.getsize(task['name'])
    return json(Resp.ok_data(task))


# 分片上传文件
@upload_task_b.post("/chunk/<session_id:str>/<chunk_cur:int>", stream=True)
@token_required(allow=[Role.Admin])
async def upload_task_chunk(request, session_id: str, chunk_cur: int, token) -> HTTPResponse:
    task = await UploadTask.get_or_none(session_id=session_id).values()
    if not task:
        return json(Resp.err(52001, None, f"上传任务不存在: {session_id}"))
    if task['mode'] != UploadMode.CHUNK.value:
        return json(Resp.err(52001, None, f"上传模式不匹配,请删除任务后重新上传"))
    chunk_info = ChunkInfo(**task['chunk_info'])
    if chunk_cur != chunk_info.chunk_cur:
        return json(Resp.err(52001, None, f"分片序号不匹配: {chunk_cur} != {chunk_info.chunk_cur}"))
    if chunk_cur >= chunk_info.chunk_total:
        return json(Resp.ok_data(task))

    sub_fs: SubFS = VFS.opendir(task['path'])

    # 失败可以重试
    if task['status'] == UploadStatus.FAILED:
        task['status'] = UploadStatus.UPLOADING
        await UploadTask.filter(session_id=session_id).update(status=UploadStatus.UPLOADING)

    if task['status'] != UploadStatus.UPLOADING:
        task['uploaded'] = sub_fs.getsize(task['name'])
        return json(Resp.ok_data(task))

    # 记录任务
    record_task = await MemCache.get_data(f"upload_{session_id}")
    if record_task is None:
        await MemCache.set_data(f"upload_{session_id}", task['id'])

    try:
        read_size = chunk_info.chunk_cur * chunk_info.chunk_size
        while True:
            body = await request.stream.read()
            record_task = await MemCache.get_data(f"upload_{session_id}")
            if record_task is None:
                try:
                    if sub_fs.exists(task['name']):
                        sub_fs.remove(task['name'])
                except:
                    pass
                await UploadTask.filter(session_id=session_id).delete()
                return json(Resp.err(52001, None, f"任务已取消"))
            if body is None:
                break
            read_size += len(body)
            real_size = sub_fs.getsize(task['name'])
            if read_size > real_size:
                sub_size = read_size - real_size
                if sub_size < len(body):
                    body = body[len(body) - sub_size:]
                sub_fs.appendbytes(task['name'], body)
            else:
                continue
        chunk_info.chunk_cur += 1
        task['chunk_info'] = chunk_info.model_dump()
        if chunk_info.chunk_cur == chunk_info.chunk_total:
            task['status'] = UploadStatus.SUCCESS
            await MemCache.del_data(f"upload_{session_id}")
            # 创建缩略图
            if AppConfig.config.preview.thumbnail:
                request.app.add_task(set_thumbnail(sub_fs.getsyspath(task['name'])))
    except Exception as e:
        task['status'] = UploadStatus.FAILED
    await UploadTask.filter(session_id=session_id).update(status=task['status'], chunk_info=task["chunk_info"])
    task['uploaded'] = sub_fs.getsize(task['name'])
    return json(Resp.ok_data(task))


# 获取任务列表
@upload_task_b.post("/list")
@token_required(allow=[Role.Admin])
async def upload_task_list(request: Request, token):
    task_list = await UploadTask.filter().all().values()
    data = []
    for t in task_list:
        if VFS.exists(forcedir(t['path']) + t['name']):
            t['uploaded'] = VFS.getsize(forcedir(t['path']) + t['name'])
        else:
            t['uploaded'] = 0
        data.append(t)
    return json(Resp.ok_data(data))


# 获取任务信息
@upload_task_b.post("/info")
@token_required(allow=[Role.Admin])
@validate(json=(upload_task_id_schema, UploadTaskIDSchema))
async def upload_task_info(request: Request, body: UploadTaskIDSchema, token) -> HTTPResponse:
    task = await UploadTask.get_or_none(session_id=body.session_id).values()
    if not task:
        return json(Resp.err_msg(f"上传任务不存在: {body.session_id}"))
    task['uploaded'] = VFS.getsize(task['path'])
    return json(Resp.ok_data(task))


# 删除上传任务单
@upload_task_b.post("/delete")
@token_required(allow=[Role.Admin])
@validate(json=(upload_task_id_schema, UploadTaskIDSchema))
async def delete_tasks(request: Request, body: UploadTaskIDSchema, token) -> HTTPResponse:
    task = await UploadTask.get_or_none(session_id=body.session_id)
    if task:
        if task.status == UploadStatus.UPLOADING:
            await cancel_task(task.session_id)
        await task.delete()
    return json(Resp.ok_msg(f"删除任务: {body.session_id}"))


# 清理任务
@upload_task_b.post("/clear")
@token_required(allow=[Role.Admin])
@validate(json=(clear_task_schema, ClearTaskSchema))
async def clear_task(request: Request, body: ClearTaskSchema, token) -> HTTPResponse:
    tasks = await UploadTask.filter(status=body.status).all()
    if tasks:
        ids = []
        for task in tasks:
            if task.status == UploadStatus.UPLOADING:
                await cancel_task(task.session_id)
            if task.status != UploadStatus.SUCCESS:
                sub = VFS.opendir(task.path)
                if sub.exists(task.name):
                    sub.remove(task.name)
            ids.append(task.id)
        await UploadTask.filter(id__in=ids).delete()
    return json(Resp.ok_msg("清理上传任务成功"))
