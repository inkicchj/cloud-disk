import os
import stat
from datetime import timedelta

import jinja2
from fs.osfs import OSFS
from json_api.magic_sanic import MagicSanic
from sanic import Sanic
from sanic_ext import Extend
from tortoise.contrib.sanic import register_tortoise

from config import AppConfig
from src.utils.authenticator import Auth
from src.utils.cache_store import MemCache
from src.utils.filesystem import VFS
from src.utils.jinja_extend import conf_app

# 创建工作文件夹
worker = os.path.abspath("")
if not os.path.exists("data"):
    os.mkdir("data")
if not os.path.exists("data/thumbnail"):
    os.mkdir("data/thumbnail")
if not os.path.exists("temp"):
    os.mkdir("temp")

# 初始化配置项
AppConfig.init("data/conf.db")

# 初始化sanic
magic = MagicSanic()
app: Sanic = Sanic("yun")

app.config.update({
    "FALLBACK_ERROR_FORMAT": "json",
    "KEEP_ALIVE_TIMEOUT": 15
})

# 模板配置
conf_app(
    app,
    jinja_template_env_name="JINJA_ENV",
    update_templates_with_its_context=True,
    update_jinja_env_globals_with=AppConfig.config,
    auto_reload=True,
    enable_async=True,
    loader=jinja2.PrefixLoader({
        "ui": jinja2.PackageLoader(__name__, "resources/templates")
    }),
)

ext = Extend(app)
magic.set_app(app)

# 初始化用户认证工具
with Auth.initialize(app) as auth_manager:
    auth_manager.config.identity_name = "id"
    auth_manager.config.token_location = ("cookies", "header", )
    auth_manager.config.token_expires = timedelta(days=7)
    auth_manager.config.token_cookie = "token"
    auth_manager.config.csrf_protect = True
    auth_manager.config.use_acl = True
    auth_manager.config.acl_claim = "role"
    auth_manager.config.check_login_ip = False

# 初始化数据库
register_tortoise(
    app,
    db_url="sqlite://data/data.db",
    modules={
        "models": [
            "src.model.storage",
            "src.model.upload_task",
            "src.model.user",
            "src.model.share",
        ]
    },
    generate_schemas=True
)

# 挂载蓝图
from src.routers import router

app.blueprint(router)

app.static("/static", "resources/static", name="uploads")


# 挂载vfs
@app.before_server_start
async def setup_vfs(app_: Sanic):
    from src.model.storage import Storage
    storages = await Storage.filter(activated=True).all()
    for s in storages:
        os.chmod(s.root_path, stat.S_IRWXG)
        VFS.mount(s.mount_name, OSFS(s.root_path, create=True))
    print("挂载目录 ->", VFS.listdir("/"))


# 挂载缓存库
@app.before_server_start
async def setup_cache(app_: Sanic):
    await MemCache.initialize()


# 初始化用户
@app.after_server_start
async def setup_user(app_: Sanic):
    from src.model.user import User, Role
    import secrets
    from passlib.hash import pbkdf2_sha256
    from passlib import pwd
    user_count = await User.all().count()
    if user_count == 0:
        admin_salt = secrets.token_hex(16)
        admin_pwd = pwd.genword(length=8)
        await User.create(
            name="admin",
            password=pbkdf2_sha256.using(rounds=20, salt=admin_salt.encode("utf-8")).hash(admin_pwd),
            role=Role.Admin,
            salt=admin_salt,
            activated=True
        )
        print("管理员账户: admin", "管理员密码: ", admin_pwd)
