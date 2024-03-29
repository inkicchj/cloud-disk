from enum import Enum

from tortoise import Model, fields


class Role(str, Enum):
    Admin = "Admin"
    User = "User"
    Guest = "Guest"


class User(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(unique=True, null=False, max_length=200, description="用户名")
    password = fields.TextField(null=True, description="用户密码")
    base_path = fields.CharField(max_length=200, default="/", description="基础路径")
    role = fields.CharEnumField(Role, description="用户角色")
    salt = fields.CharField(null=False, max_length=200, description="盐值")
    activated = fields.BooleanField(default=False, null=False, description="激活状态")
