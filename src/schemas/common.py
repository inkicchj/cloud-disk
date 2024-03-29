from urllib.parse import unquote

from fs.path import forcedir, normpath, abspath
from voluptuous import All, Strip, Length, Match, Invalid

from src.utils.filesystem import VFS

def parse(v):
    if isinstance(v, list):
        return unquote(v[0], encoding="utf-8")
    if isinstance(v, str):
        return v



def validate_name(name: str) -> str:
    exc = ["/", "\\", ":", "\"", "?", "*", "<", ">", "|"]
    for e in exc:
        if e in name:
            raise Invalid(f'名称不能包含 [\\/:"?*<>|]')
    return name


def regular_path(path: str) -> str:
    path_ = abspath(forcedir(normpath(path)))
    if not VFS.exists(path):
        raise Invalid(f"路径不存在: {path_}")
    if VFS.isfile(path_):
        if path_.endswith("/"):
            path_ = path_[0:-1]
    return path_


def operate_path(path: str) -> str:
    if path == "/":
        raise Invalid(f"路径无法操作: /")
    return path


path_rule = All(
    str,
    Strip,
    Length(max=100, msg="路径最大长度为100"),
    Match(r"^/([\w\.]+\/?)*", msg=r"路径格式不匹配: '^/([\w\.]+\/?)*'"),
)

name_rule = All(
    str,
    Strip,
    Length(max=100, msg="名称最长为100字符"),
    validate_name
)
