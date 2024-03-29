from datetime import datetime
from enum import Enum

from tortoise import Model, fields


class OrderBy(str, Enum):
    Name = "name"
    Size = "size"
    Modified = "modified"
    Created = "created"
    FileType = "file_type"


class Storage(Model):
    id = fields.IntField(pk=True)
    mount_name = fields.CharField(index=True, unique=True, null=False, max_length=200, description="挂载名称")
    root_path = fields.CharField(default="/", null=False, max_length=200, description="真实路径")
    order = fields.IntField(default=0, null=False, description="排序")
    order_field = fields.CharEnumField(OrderBy, default=OrderBy.Name, null=False, description="排序字段")
    reverse = fields.BooleanField(default=False, null=False, description="升序or降序")
    capacity = fields.IntField(default=1024 * 1024 * 1024 * 10, null=False, description="存储容量")
    activated = fields.BooleanField(default=True, null=False, description="激活状态")
    created = fields.FloatField(default=datetime.now().timestamp(), null=False, description="创建时间")
    modified = fields.FloatField(default=datetime.now().timestamp(), null=False, description="修改时间")
