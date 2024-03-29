from voluptuous import Schema, All, Required, Object, Range, Strip, Length, Invalid

from src.utils.filesystem import VFS
from .common import path_rule, name_rule, regular_path, operate_path, parse


class ListsSchema:
    def __init__(self, path: str, page: int):
        self.path = path
        self.page = page


lists_schema = Schema(

    Object(
        {
            Required("path", default="/"): All(path_rule, regular_path),
            Required('page', default=1): All(
                int,
                Range(min=1, max=200, msg=r"页码范围为1~200")
            )
        },
        cls=ListsSchema
    )
)


class PathSchema:
    def __init__(self, path=None):
        self.path = path


path_schema = Schema(
    Object(
        {
            Required("path", msg="路径不能为空"): All(
                parse,
                path_rule,
                regular_path,
                operate_path
            )
        },
        cls=PathSchema
    )
)


class ActionPathSchema:
    def __init__(self, path=None, name=None):
        self.path = path
        self.name = name


action_path_schema = Schema(
    Object(
        {
            Required("path", msg="路径不能为空"): All(
                path_rule,
                regular_path,
                operate_path
            ),
            Required("name", msg="名称不能为空"): name_rule
        },
        cls=ActionPathSchema
    )
)


class CopyAndMoveSchema:
    def __init__(self, src_dir: str = None, dst_dir: str = None, name: list = None):
        self.src_dir = src_dir
        self.dst_dir = dst_dir
        self.name = name


def parse_cm(n: CopyAndMoveSchema):
    names = []
    names_1 = []
    for name_ in n.name:
        if VFS.exists(n.src_dir + name_):
            names.append(name_)
        if not VFS.exists(n.dst_dir + name_):
            names_1.append(name_)
    n.name = list(set(names) & set(names_1))
    return n


copy_and_move_schema = Schema(
    All(
        Object(
            {
                Required("src_dir", msg="源文件夹路径不能为空"): All(
                    path_rule,
                    regular_path,
                    operate_path
                ),
                Required("dst_dir", msg="目标文件夹路径不能为空"): All(
                    path_rule,
                    regular_path,
                    operate_path
                ),
                Required("name"): [name_rule]
            },
            cls=CopyAndMoveSchema
        ),
        parse_cm

    )
)


class NameListOneDirSchema:
    def __init__(self, src_dir=None, name=None):
        self.src_dir = src_dir
        self.name = name


def parse_one_l(n: NameListOneDirSchema):
    names = []
    for name_ in n.name:
        if VFS.exists(n.src_dir + name_):
            names.append(name_)
    n.name = names
    return n


name_list_one_dir_schema = Schema(
    All(
        Object(
            {
                Required("src_dir", msg="源文件夹路径不能为空"): All(
                    path_rule,
                    regular_path,
                    operate_path
                ),
                Required("name"): [name_rule]
            },
            cls=NameListOneDirSchema
        ),
        parse_one_l

    )
)


class SearchSchema:
    def __init__(self, path=None, name=None, is_dir=None, page=None):
        self.path = path
        self.name = name
        self.is_dir = is_dir
        self.page = page


def validate_search_name(name: str) -> str:
    exc = ["/", "\\", ":", "\"", "?", "<", ">", "|"]
    for e in exc:
        if e in name:
            raise Invalid(f'名称不能包含 [\\/:"?<>|]')
    return name


search_schema = Schema(
    Object(
        {
            Required("path", msg="路径不能为空"): All(
                path_rule,
                regular_path
            ),
            Required("name", msg="名称不能为空"): All(
                str,
                Strip,
                Length(max=30, msg="名称最长为30字符"),
                validate_search_name
            ),
            Required("is_dir", msg="类型不能为空"): bool,
            Required('page', default=1): All(
                int,
                Range(min=1, max=200, msg=r"页码范围为1~200")
            )
        },
        cls=SearchSchema
    )
)
