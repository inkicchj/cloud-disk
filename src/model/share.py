from datetime import timedelta
from enum import Enum

from tortoise import Model, fields


class Expired(Enum):
    OneDay = timedelta(days=1).total_seconds()
    SevenDay = timedelta(days=7).total_seconds()
    FifteenDay = timedelta(days=15).total_seconds()
    Forever = -1.0


class Share(Model):
    id = fields.IntField(pk=True)
    mark = fields.CharField(max_length=30, unique=True, description="分享标识码")
    path = fields.CharField(max_length=100, description="关联路径")
    is_dir = fields.BooleanField(description="是否为目录")
    password = fields.CharField(max_length=10, description="密码")
    expired = fields.FloatField(null=True, description="过期时间")
