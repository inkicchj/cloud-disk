from mimetypes import guess_type
from os import path
from pathlib import PurePath
from typing import TypeVar, Union, Optional, Dict

from aiofiles import os
from sanic.compat import open_async
from sanic.models.protocol_types import Range
from sanic.response import ResponseStream

from config import AppConfig
from config import PaginationMode

T = TypeVar('T')


class Resp:

    @classmethod
    def ok_data(cls, data: T) -> dict:
        return dict(code=200, data=data, message=None)

    @classmethod
    def ok_msg(cls, message: str) -> dict:
        return dict(code=200, data=None, message=message)

    @classmethod
    def ok(cls, code: int, data: T, message: str) -> dict:
        return dict(code=code, data=data, message=message)

    @classmethod
    def err_data(cls, data: T) -> dict:
        return dict(code=410, data=data, message=None)

    @classmethod
    def err_msg(cls, message: str) -> dict:
        return dict(code=410, data=None, message=message)

    @classmethod
    def err(cls, code: int, data: T, message: str) -> dict:
        return dict(code=code, data=data, message=message)

    @classmethod
    def paginate(cls, cur, total, data, mode=None) -> dict:
        page_size = AppConfig.config.fs.pagination_size
        total_page = int(total / page_size) if total == page_size else (int(total / page_size) + 1)

        pagination_list = []
        if mode and mode == PaginationMode.Manual.value:
            column = 5
            if total_page <= column:
                pagination_list.extend([i for i in range(1, total_page + 1)])
            else:
                page_list = []
                page_list.extend([i for i in range(1, total_page + 1)])
                center = column / 2 + 1
                show_pages = []
                if cur < center:
                    show_pages.extend(page_list[0:column])
                elif center <= cur <= (total_page - center + 1):
                    show_pages.extend(page_list[cur - center: (cur + center - 1)])
                elif cur > (total_page - center + 1):
                    show_pages.extend(page_list[total_page - column: total_page])
                pagination_list.extend(show_pages)
            page_start = (cur - 1) * page_size
            if page_start > len(data):
                data = []
            else:
                page_end = cur * page_size
                page_end = page_end if page_end <= len(data) else len(data)
                data = data[page_start:page_end]

        return dict(
            page=cur,
            pages=pagination_list,
            total_page=total_page,
            data=data
        )


async def file_stream(
        location: Union[str, PurePath],
        status: int = 200,
        chunk_size: int = 4096,
        mime_type: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        filename: Optional[str] = None,
        _range: Optional[Range] = None,
        del_file: bool = False
) -> ResponseStream:
    headers = headers or {}
    if filename:
        headers.setdefault(
            "Content-Disposition", f'attachment; filename="{filename}"'
        )
    filename = filename or path.split(location)[-1]
    mime_type = mime_type or guess_type(filename)[0] or "text/plain"
    if _range:
        start = _range.start
        end = _range.end
        total = _range.total

        headers["Content-Range"] = f"bytes {start}-{end}/{total}"
        status = 206

    async def _streaming_fn(response):
        async with await open_async(location, mode="rb") as f:
            if _range:
                await f.seek(_range.start)
                to_send = _range.size
                while to_send > 0:
                    content = await f.read(min((_range.size, chunk_size)))
                    if len(content) < 1:
                        break
                    to_send -= len(content)
                    await response.write(content)
            else:
                while True:
                    content = await f.read(chunk_size)
                    if len(content) < 1 or content is None:
                        break
                    await response.write(content)

        if del_file:
            await os.remove(location)

    return ResponseStream(
        streaming_fn=_streaming_fn,
        status=status,
        headers=headers,
        content_type=mime_type,
    )
