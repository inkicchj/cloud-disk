from pathlib import Path

from src.model.storage import OrderBy
from voluptuous import Schema, Object, All, Required, Range, In, Boolean, Match
from voluptuous.error import Invalid
from .common import path_rule, name_rule
from math import pow

dir_match = r'(^\/([^\/]+\/?)*$)|(^([a-zA-Z]:)(\\[^/\\:*?"<>|]+\\?)*$)'

def regular_path(path: str) -> str:
    if not Path(path).exists():
        raise Invalid(f"系统路径不存在: {path}")
    return path


class NewStorageSchema:
    def __init__(self, mount_name=None, root_path=None, order=None, capacity=None, order_field=None, reverse=None):
        self.mount_name = mount_name
        self.root_path = root_path
        self.order = order
        self.capacity = capacity
        self.order_field = order_field
        self.reverse = reverse


new_storage_schema = Schema(Object({
    Required("mount_name", msg="挂载名称不能为空"): name_rule,
    Required("root_path", msg="系统路径不能为空"): All(str, Match(dir_match, "系统路径格式不正确")),
    Required("order", default=0): All(int, Range(min=0, max=100, msg="排序范围为1~100")),
    Required("capacity", default=pow(1024, 4)): All(
        int,
        Range(min=0, max=pow(1024, 4), msg=f"存储容量范围为0~{pow(1024, 4)}")
    ),
    Required("order_field", default=OrderBy.Name): All(
        str,
        In(container=[ob.value for ob in list(OrderBy)], msg=f"值必须为其中之一: {[ob.value for ob in list(OrderBy)]}")
    ),
    Required("reverse"): Boolean()
}, cls=NewStorageSchema))


class UpdateStorageSchema:
    def __init__(self, id, mount_name=None, root_path=None, order=None, capacity=None, order_field=None, reverse=None):
        self.id = id
        self.mount_name = mount_name
        self.root_path = root_path
        self.order = order
        self.capacity = capacity
        self.order_field = order_field
        self.reverse = reverse


update_storage_schema = Schema(Object({
    Required("id"): int,
    Required("mount_name", msg="挂载名称不能为空"): name_rule,
    Required("root_path", msg="系统路径不能为空"): All(path_rule, regular_path),
    Required("order", default=0): All(int, Range(min=0, max=100, msg="排序范围为1~100")),
    Required("capacity", default=pow(1024, 4)): All(
        int,
        Range(min=0, max=pow(1024, 4), msg=f"存储容量范围为0~{pow(1024, 4)}")
    ),
    Required("order_field", default=OrderBy.Name): All(
        str,
        In(container=[ob.value for ob in list(OrderBy)], msg=f"值必须为其中之一: {[ob.value for ob in list(OrderBy)]}")
    ),
    Required("reverse"): Boolean()
}, cls=UpdateStorageSchema))


class StorageIDSchema:
    def __init__(self, id=None):
        self.id = id


storage_id_schema = Schema(Object({
    Required("id"): int,
}, cls=StorageIDSchema))

