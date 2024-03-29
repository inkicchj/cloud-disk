from fs.path import abspath, forcedir, normpath
from voluptuous import Schema, Object, Required, All, Length, Range, In, Coerce

from src.model.share import Expired
from .common import path_rule, regular_path, operate_path, parse


class NewShareSchema:
    def __init__(self, path=None, password=None, expired=None):
        self.path = path
        self.password = password
        self.expired = expired


new_share_schema = Schema(
    Object(
        {
            Required("path", msg="路径不能为空"): All(
                path_rule,
                regular_path,
                operate_path
            ),
            Required("password"): All(
                str,
                Length(max=4, msg="密码最长为4个字符")
            ),
            Required("expired", msg="过期时间不能为空"): In(container=[e.name for e in list(Expired)])
        },
        cls=NewShareSchema
    )
)


class ListShareSchema:
    def __init__(self, page=None):
        self.page = page


list_share_schema = Schema(Object({
    Required("page", default=1): All(int, Range(min=1, max=200))
}, cls=ListShareSchema))


class ShareIDSchema:
    def __init__(self, id=None):
        self.id = id


share_id_schema = Schema(Object({
    Required("id"): int
}, cls=ShareIDSchema))


def regular_view_path(path: str) -> str:
    path_ = abspath(forcedir(normpath(path)))
    return path_


class PublicShareSchema:
    def __init__(self, mark: str = None, path: str = None, password: str = None):
        self.mark = mark
        self.path = path
        self.password = password


public_share_schema = Schema(Object({
    Required("mark"): All(str, Length(max=30)),
    Required("path", default="/"): All(parse, path_rule, regular_view_path),
    Required("password", default=""): All(str, Length(max=4))
}, cls=PublicShareSchema))
